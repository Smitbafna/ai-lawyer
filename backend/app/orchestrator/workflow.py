"""
Main intake workflow: coordinates LLM extraction, case merging, and persistence.
"""

import logging
from typing import Any

from app.agents.intake import IntakeAgent, IntakeLLMOutput
from app.database.connection import SessionLocal
from app.database.models import Case, Conversation, Message
from app.services.case_service import update_case_facts
from app.services.conversation_service import add_message, get_or_create_conversation

logger = logging.getLogger(__name__)


class IntakeWorkflow:
    def __init__(self, intake_agent: IntakeAgent):
        self.intake_agent = intake_agent

    def _get_conversation_history(
        self, db: SessionLocal, conversation: Conversation
    ) -> list[dict[str, str]]:
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        return [{"role": m.role, "content": m.content} for m in messages]

    async def process_message(
        self, case_id: str, user_message: str
    ) -> dict[str, Any]:
        db = SessionLocal()
        try:
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise ValueError(f"Case {case_id} not found")

            conversation = get_or_create_conversation(db, case_id)

            # Persist user message
            add_message(db, conversation.id, "user", user_message)

            # Get conversation history
            history = self._get_conversation_history(db, conversation)

            # Run intake agent
            llm_output: IntakeLLMOutput = await self.intake_agent.run(
                user_message, case, history
            )

            # Merge new facts into existing case
            existing_facts = case.structured_facts or {}
            merged_facts = IntakeAgent.merge_updates(existing_facts, llm_output.extracted_updates)

            # Compute missing information
            missing_info = llm_output.missing_information or []

            # Update case in DB
            update_case_facts(db, case_id, merged_facts, missing_info)

            # Persist assistant response
            assistant_message = llm_output.assistant_message or ""
            add_message(db, conversation.id, "assistant", assistant_message)

            # Refresh case for response
            db.refresh(case)

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
                    "created_at": str(case.created_at) if case.created_at else None,
                    "updated_at": str(case.updated_at) if case.updated_at else None,
                },
                "missing_information": case.missing_information or [],
                "intake_status": case.status,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()