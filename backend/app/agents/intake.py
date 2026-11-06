"""
Intake agent: extracts structured facts from user messages, merges them into
the existing case, identifies missing information, and produces follow-up questions.
"""

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.database.models import Case
from app.llm.provider import LLMProvider, LLMProviderError

logger = logging.getLogger(__name__)


class IntakeLLMOutput(BaseModel):
    """Structured output the LLM must return for each intake turn."""

    extracted_updates: dict[str, Any] = Field(
        default_factory=dict,
        description="Partial structured_facts updates from this turn only.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Fields still missing from the case.",
    )
    follow_up_question: Optional[str] = Field(
        default=None,
        description="One contextual follow-up question, or None if none needed.",
    )
    intake_status: str = Field(
        default="intake_in_progress",
        description="Either 'intake_in_progress' or 'intake_complete'.",
    )
    assistant_message: str = Field(
        default="",
        description="Natural-language response to the user.",
    )


class IntakeAgent:
    def __init__(self, llm_provider: LLMProvider[IntakeLLMOutput]):
        self.llm = llm_provider

    def _build_system_prompt(self) -> str:
        return (
            "You are an intake assistant for a tenant-landlord dispute case in India. "
            "The dispute type is 'security_deposit_dispute'. "
            "Your job is to extract structured facts from the user's natural-language "
            "description and identify what information is still missing. "
            "\n\n"
            "You must return a JSON object with these fields:\n"
            "- extracted_updates: an object containing only the NEW facts learned in THIS turn. "
            "  Use these keys when applicable: jurisdiction.state, jurisdiction.city, "
            "  parties.tenant, parties.landlord, property_address, rental_start_date, "
            "  rental_end_date, vacating_date, security_deposit_amount, "
            "  security_deposit_currency, deposit_payment_date, deposit_payment_method, "
            "  rental_agreement_exists, refund_clause, landlord_response, facts (array of strings), "
            "  timeline (array of {date, event} objects), evidence_available (array of strings).\n"
            "- missing_information: array of field descriptions still missing and needed.\n"
            "- follow_up_question: ONE short natural-language question to ask the user, "
            "  or null if no follow-up is needed. Ask only one question at a time.\n"
            "- intake_status: 'intake_in_progress' or 'intake_complete'.\n"
            "- assistant_message: a friendly natural-language response to the user.\n"
            "\n"
            "Rules:\n"
            "1. Do NOT invent values. Only include what the user explicitly provided.\n"
            "2. Do NOT ask for information already provided.\n"
            "3. Ask only the most important missing piece first.\n"
            "4. Prioritize: state/city, rental agreement, deposit details, vacating date, "
            "   refund clause, landlord's explanation.\n"
            "5. Return ONLY the JSON object, no markdown fences, no extra text.\n"
        )

    def _build_user_prompt(
        self,
        user_message: str,
        existing_facts: dict[str, Any],
        existing_missing: list[str],
        conversation_history: list[dict[str, str]],
    ) -> str:
        history_text = ""
        if conversation_history:
            history_text = "\nConversation history:\n"
            for msg in conversation_history[-10:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"

        return (
            f"User message: {user_message}"
            + history_text
            + f"\n\nExisting structured case facts: {json.dumps(existing_facts, default=str, ensure_ascii=False)}"
            + f"\nExisting missing information: {json.dumps(existing_missing, ensure_ascii=False)}"
            + "\n\nExtract any NEW facts from this user message and merge them conceptually "
            "with the existing facts. Return only the NEW updates in extracted_updates."
        )

    async def run(
        self,
        user_message: str,
        existing_case: Case,
        conversation_history: list[dict[str, str]],
    ) -> IntakeLLMOutput:
        existing_facts = existing_case.structured_facts or {}
        existing_missing = existing_case.missing_information or []

        prompt = self._build_user_prompt(
            user_message, existing_facts, existing_missing, conversation_history
        )

        try:
            result: IntakeLLMOutput = await self.llm.generate_structured_output(
                prompt, IntakeLLMOutput, system_prompt=self._build_system_prompt()
            )
        except LLMProviderError:
            raise
        except Exception as exc:
            logger.error("Unexpected error in intake agent: %s", exc)
            raise LLMProviderError(str(exc)) from exc

        return result

    @staticmethod
    def merge_updates(
        existing_facts: dict[str, Any], updates: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge new extracted updates into existing facts without overwriting known
        non-null values with null or empty values.
        """
        merged = dict(existing_facts)

        def _merge_dict(dst: dict[str, Any], src: dict[str, Any]) -> None:
            for key, value in src.items():
                if value is None:
                    continue
                if isinstance(value, dict) and isinstance(dst.get(key), dict):
                    _merge_dict(dst[key], value)
                elif isinstance(value, list) and key in (
                    "facts",
                    "timeline",
                    "evidence_available",
                    "missing_information",
                ):
                    existing_list = dst.get(key, [])
                    if not isinstance(existing_list, list):
                        existing_list = []
                    for item in value:
                        if item not in existing_list:
                            existing_list.append(item)
                    dst[key] = existing_list
                else:
                    current = dst.get(key)
                    if current is None or current == "" or current == []:
                        dst[key] = value

        _merge_dict(merged, updates)
        return merged