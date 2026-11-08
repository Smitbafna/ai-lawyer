"""
Intake agent: extracts structured facts from user messages, merges them into
the existing case, identifies missing information, and produces follow-up questions.
"""

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.database.models import Case
from .llm.provider import LLMProvider, LLMProviderError

logger = logging.getLogger(__name__)


class IntakeLLMOutput(BaseModel):
    """Structured output the LLM must return for each intake turn."""

    extracted_updates: dict[str, Any] = Field(
        default_factory=dict,
        description="Partial structured_facts updates from this turn only. "
        "Only new facts that do not conflict with existing values.",
    )
    corrections: dict[str, Any] = Field(
        default_factory=dict,
        description="Fields the user is explicitly correcting. "
        "These overwrite existing values after confirmation.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="Fields still missing from the case.",
    )
    confirmation_needed: list[str] = Field(
        default_factory=list,
        description="Field paths where new info conflicts with existing facts "
        "and the user must confirm which value is correct.",
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
            "- extracted_updates: an object containing only the NEW facts learned in THIS turn "
            "  that do NOT conflict with existing values. "
            "  Use these keys when applicable: jurisdiction.state, jurisdiction.city, "
            "  parties.tenant, parties.landlord, property_address, rental_start_date, "
            "  rental_end_date, vacating_date, security_deposit_amount, "
            "  security_deposit_currency, deposit_payment_date, deposit_payment_method, "
            "  rental_agreement_exists, refund_clause, landlord_response, facts (array of strings), "
            "  timeline (array of {date, event} objects), evidence_available (array of strings).\n"
            "- corrections: an object containing fields the user is EXPLICITLY CORRECTING. "
            "  Use this only when the user clearly contradicts a previously stated fact "
            "  (e.g., \"actually it was 30000 not 25000\"). These overwrite existing values.\n"
            "- missing_information: array of field descriptions still missing and needed.\n"
            "- confirmation_needed: array of field paths where the new information conflicts "
            "  with an existing fact but the user has not clearly stated they are correcting. "
            "  Ask the user to confirm which value is correct.\n"
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
            "5. If the user contradicts a previous fact without clearly correcting it, "
            "  put the field in confirmation_needed, not in corrections.\n"
            "6. Return ONLY the JSON object, no markdown fences, no extra text.\n"
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

    # System-controlled fields that must never be modified by LLM extraction or user input
    _SYSTEM_FIELDS = frozenset(
        {
            "id",
            "case_id",
            "case_type",
            "status",
            "owner",
            "ownership",
            "created_at",
            "updated_at",
            "version",
        }
    )

    @staticmethod
    def _strip_system_fields(updates: dict[str, Any]) -> dict[str, Any]:
        """Remove system-controlled fields from LLM-provided updates (recursively)."""
        if not isinstance(updates, dict):
            return updates
        result: dict[str, Any] = {}
        for key, value in updates.items():
            if key in IntakeAgent._SYSTEM_FIELDS:
                continue
            if isinstance(value, dict):
                result[key] = IntakeAgent._strip_system_fields(value)
            elif isinstance(value, list):
                result[key] = [
                    IntakeAgent._strip_system_fields(item)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    @staticmethod
    def _detect_conflicts(
        existing: dict[str, Any],
        updates: dict[str, Any],
        corrections: dict[str, Any],
        prefix: str = ""
    ) -> list[str]:
        """Recursively detect field paths where updates conflict with existing non-null values.

        A conflict exists when:
        - updates has a non-null value for a key
        - existing already has a different non-null value for that key
        - the key is NOT in corrections (corrections are intentional overwrites)
        """
        conflicts: list[str] = []
        for key, new_val in updates.items():
            if new_val is None:
                continue
            path = f"{prefix}.{key}" if prefix else key
            if key in corrections:
                continue  # corrections are intentional overwrites, not conflicts
            existing_val = existing.get(key)
            if existing_val is not None and existing_val != "" and existing_val != []:
                if isinstance(new_val, dict) and isinstance(existing_val, dict):
                    conflicts.extend(
                        IntakeAgent._detect_conflicts(
                            existing_val, new_val, corrections.get(key, {}), prefix=path
                        )
                    )
                elif new_val != existing_val:
                    conflicts.append(path)
        return conflicts

    @staticmethod
    def merge_updates(
        existing_facts: dict[str, Any],
        updates: dict[str, Any],
        corrections: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Merge new extracted updates into existing facts.

        Rules:
        - corrections: ALWAYS overwrite existing values (intentional user corrections).
        - extracted_updates: only fill null/empty existing values.
        - Conflicts (non-null existing value != new value, not in corrections)
          are preserved and reported as needing confirmation.

        Returns (merged_facts, conflict_paths).
        """
        corrections = corrections or {}
        updates = IntakeAgent._strip_system_fields(updates)
        corrections = IntakeAgent._strip_system_fields(corrections)

        merged = dict(existing_facts)

        # Detect conflicts BEFORE merging (based on extracted_updates only)
        conflicts = IntakeAgent._detect_conflicts(merged, updates, corrections)

        def _merge_force(dst: dict[str, Any], src: dict[str, Any]) -> None:
            """Merge that always overwrites (used for corrections)."""
            for key, value in src.items():
                if value is None:
                    continue
                if isinstance(value, dict) and isinstance(dst.get(key), dict):
                    _merge_force(dst[key], value)
                elif isinstance(value, list) and key in (
                    "facts", "timeline", "evidence_available", "missing_information",
                ):
                    existing_list = dst.get(key, [])
                    if not isinstance(existing_list, list):
                        existing_list = []
                    for item in value:
                        if item not in existing_list:
                            existing_list.append(item)
                    dst[key] = existing_list
                else:
                    dst[key] = value  # always overwrite

        def _merge_fill(dst: dict[str, Any], src: dict[str, Any]) -> None:
            """Merge that only fills null/empty (used for extracted_updates)."""
            for key, value in src.items():
                if value is None:
                    continue
                if isinstance(value, dict) and isinstance(dst.get(key), dict):
                    _merge_fill(dst[key], value)
                elif isinstance(value, list) and key in (
                    "facts", "timeline", "evidence_available", "missing_information",
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

        # Apply corrections first (they overwrite existing values unconditionally)
        _merge_force(merged, corrections)

        # Apply extracted_updates (only fill null/empty)
        _merge_fill(merged, updates)

        return merged, conflicts