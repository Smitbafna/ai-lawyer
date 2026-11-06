"""
Main intake workflow: coordinates LLM extraction, case merging, and persistence.

Database writes for a single conversational turn happen inside one transaction.
The LLM call is made *outside* any transaction so a slow or failing LLM never
holds a DB connection open and never leaves partial writes.
"""

import logging
from typing import Any

from app.agents.intake import IntakeAgent, IntakeLLMOutput
from app.database.connection import SessionLocal
from app.database.models import Case, Conversation, Message
from app.services.case_service import update_case_facts
from app.services.conversation_service import add_message, get_or_create_conversation

logger = logging.getLogger(__name__)

# Fields that are system-controlled and must never be overwritten by LLM output
_SYSTEM_FIELDS = frozenset(
    {"id", "case_id", "case_type", "status", "owner", "ownership", "created_at", "updated_at", "version"}
)


class IntakeWorkflow:
    def __init__(self, intake_agent: IntakeAgent):
        self.intake_agent = intake_agent

    def _get_conversation_history(
        self, db, conversation: Conversation
    ) -> list[dict[str, str]]:
        if conversation is None:
            return []
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        return [{"role": m.role, "content": m.content} for m in messages]

    def _build_provenance(
        self,
        existing_provenance: dict[str, Any],
        llm_output: IntakeLLMOutput,
        turn_index: int,
    ) -> dict[str, Any]:
        """Build updated fact_provenance from LLM output."""
        prov = dict(existing_provenance or {})

        # Model-extracted facts
        for field_path in (llm_output.extracted_updates or {}):
            prov[field_path] = {
                "source": "model",
                "confirmed": False,
                "turn": turn_index,
            }

        # User corrections are explicitly confirmed
        for field_path in (llm_output.corrections or {}):
            prov[field_path] = {
                "source": "user",
                "confirmed": True,
                "turn": turn_index,
            }

        return prov

    async def process_message(
        self, case_id: str, user_message: str, db=None
    ) -> dict[str, Any]:
        own_session = db is None
        if own_session:
            db = SessionLocal()
        try:
            # 1. Read phase (short transaction).
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise ValueError(f"Case {case_id} not found")

            conversation = (
                db.query(Conversation).filter(Conversation.case_id == case_id).first()
            )
            history = self._get_conversation_history(db, conversation)

            current_version = case.version or 1
            existing_facts = case.structured_facts or {}
            existing_missing = case.missing_information or []
            existing_provenance = case.fact_provenance or {}
            case_type = case.case_type
            case_status = case.status

            # Release the read transaction before the (potentially slow) LLM call.
            db.commit()

            # 2. Transient case view for the LLM (no DB attached).
            transient_case = Case(
                id=case_id,
                case_type=case_type,
                status=case_status,
                structured_facts=existing_facts,
                missing_information=existing_missing,
            )

            # 3. Call LLM OUTSIDE any transaction.
            llm_output: IntakeLLMOutput = await self.intake_agent.run(
                user_message, transient_case, history
            )

            # 4. Merge facts and detect conflicts
            merged_facts, detected_conflicts = IntakeAgent.merge_updates(
                existing_facts,
                llm_output.extracted_updates,
                llm_output.corrections,
            )

            # 5. Combine LLM-flagged confirmations with detected conflicts
            confirmation_needed = list(
                set((llm_output.confirmation_needed or []) + detected_conflicts)
            )

            # 6. Build provenance
            provenance = self._build_provenance(
                existing_provenance, llm_output, current_version
            )

            # 7. Compute missing information
            missing_info = llm_output.missing_information or []

            # 8. Persist the successful turn atomically.
            conversation = get_or_create_conversation(db, case_id)

            add_message(db, conversation.id, "user", user_message)

            updated_case = update_case_facts(
                db,
                case_id,
                merged_facts,
                missing_info,
                fact_provenance=provenance,
                expected_version=current_version,
            )

            assistant_message = llm_output.assistant_message or ""
            add_message(db, conversation.id, "assistant", assistant_message)

            # Single commit for the entire turn
            db.commit()

            if updated_case is not None:
                db.refresh(updated_case)
                case = updated_case
            else:
                case = db.query(Case).filter(Case.id == case_id).first()

            return {
                "assistant_message": assistant_message,
                "updated_case": {
                    "id": case.id,
                    "case_type": case.case_type,
                    "jurisdiction_state": case.jurisdiction_state,
                    "jurisdiction_city": case.jurisdiction_city,
                    "status": case.status,
                    "structured_facts": case.structured_facts,
                    "missing_information": case.missing_information,
                    "fact_provenance": case.fact_provenance,
                    "version": case.version,
                    "created_at": str(case.created_at) if case.created_at else None,
                    "updated_at": str(case.updated_at) if case.updated_at else None,
                },
                "missing_information": case.missing_information or [],
                "intake_status": case.status,
                "confirmation_needed": confirmation_needed,
            }
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
            raise
        finally:
            if own_session:
                db.close()
