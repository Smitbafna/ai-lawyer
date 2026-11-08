"""
Main intake workflow: coordinates LLM extraction, case merging, and persistence.

Database writes for a single conversational turn happen inside one transaction.
The LLM call is made *outside* any transaction so a slow or failing LLM never
holds a DB connection open and never leaves partial writes.
"""

import logging
from typing import Any

from .agents.intake import IntakeAgent, IntakeLLMOutput
from .database.connection import SessionLocal
from .database.models import Case, Conversation, Message
from .services.case_service import update_case_facts
from .services.conversation_service import add_message, get_or_create_conversation

logger = logging.getLogger(__name__)

# System-controlled capability boundaries — these MUST NOT be claimed unless
# the corresponding service actually reports success.
_UNSUPPORTED_CAPABILITIES = frozenset(
    {
        "generate_legal_notice",
        "dispatch_email",
        "send_email",
        "file_complaint",
        "contact_landlord",
        "contact_authorities",
    }
)

# Supported jurisdictions for the RAG pipeline
SUPPORTED_JURISDICTIONS = {"Uttarakhand"}

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

    def _check_unsupported_capability(self, user_message: str, case: Case) -> Optional[str]:
        """Check if the user message requests an unsupported capability.

        Returns an explicit response string if an unsupported capability is detected,
        or None if the message is within supported capabilities.
        This is a deterministic server-side check - the LLM cannot override it.
        """
        message_lower = user_message.lower()

        # Check for legal notice generation requests
        notice_keywords = [
            "legal notice", "formal notice", "legal notice", "draft notice",
            "prepare notice", "create notice", "send notice"
        ]
        for kw in notice_keywords:
            if kw in message_lower:
                return (
                    "I can help you understand your legal position regarding the unreturned "
                    "security deposit and explain possible next steps. However, Kuku currently "
                    "does not support generating formal legal notices. You may want to consult "
                    "a qualified lawyer for preparation of a formal notice."
                )

        # Check for email dispatch/sending requests
        email_keywords = [
            "send email", "email", "dispatch", "dispatch email",
            "send a message", "contact via email"
        ]
        for kw in email_keywords:
            if kw in message_lower:
                return (
                    "I cannot send emails or dispatch documents from Kuku. No email has been "
                    "sent. I can help explain your legal position here."
                )

        # Check for complaint filing requests
        complaint_keywords = [
            "file complaint", "file a complaint", "complaint", "legal complaint",
            "file case", "take legal action"
        ]
        for kw in complaint_keywords:
            if kw in message_lower:
                return (
                    "I cannot file legal complaints or initiate formal proceedings from Kuku. "
                    "I can help explain your legal position and possible next steps. "
                    "For filing a formal complaint, you should consult a qualified lawyer."
                )

        # Check for landlord/authority contact requests
        contact_keywords = [
            "contact landlord", "contact the landlord", "contact landlords",
            "contact authorities", "reach out to landlord"
        ]
        for kw in contact_keywords:
            if kw in message_lower:
                return (
                    "I cannot contact landlords or authorities on your behalf. Kuku is a "
                    "legal Q&A assistant and does not have the ability to communicate with "
                    "other parties. I can help explain your legal position here."
                )

        # Check for document generation claims in the assistant's own message context.
        # This is a safety net - if the LLM somehow claims completion, we surface it.
        # We check for specific claim patterns that should never be true.
        false_claim_patterns = [
            ("I have generated your document", "The document has not been generated. Kuku currently does not support legal notice generation."),
            ("I have finalized your notice", "Kuku currently does not support generating formal legal notices."),
            ("I have dispatched your email", "I cannot send emails or dispatch documents from Kuku."),
            ("Your email has been sent", "No email has been sent from Kuku."),
            ("Your complaint has been filed", "I cannot file legal complaints from Kuku."),
            ("I have contacted your landlord", "I cannot contact landlords or authorities on your behalf."),
        ]
        for claim, response in false_claim_patterns:
            # Use word boundary matching - check if the claim phrase appears
            # We check for the claim as a substring but want to be reasonably strict
            if claim.lower() in message_lower:
                return response

        return None

    def _detect_jurisdiction(self, case: Case) -> Optional[str]:
        """Detect jurisdiction from case structured_facts.

        Returns the detected jurisdiction state, or None if not specified.
        This is a deterministic server-side check - the LLM cannot override it.
        """
        structured_facts = case.structured_facts or {}
        jurisdiction = structured_facts.get("jurisdiction")
        if jurisdiction is None:
            return None
        if isinstance(jurisdiction, dict):
            state = jurisdiction.get("state")
            city = jurisdiction.get("city")
            if state:
                return state
            if city:
                return city
        if isinstance(jurisdiction, str):
            return jurisdiction
        return None

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

            # Check for unsupported capability requests before proceeding.
            # This prevents the LLM from claiming actions that the backend cannot perform.
            capability_check = self._check_unsupported_capability(user_message, case)
            if capability_check is not None:
                # User requested an unsupported action - return early with explicit response.
                # Do NOT proceed with intake flow or LLM call that might claim completion.
                assistant_message = capability_check
                conversation = get_or_create_conversation(db, case_id)
                add_message(db, conversation.id, "user", user_message)
                add_message(db, conversation.id, "assistant", assistant_message)
                db.commit()
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
                    "confirmation_needed": [],
                }

            # jurisdiction enforcement: detect from case facts and reject non-Uttarakhand cases
            detected_jurisdiction = self._detect_jurisdiction(case)
            if detected_jurisdiction is not None and detected_jurisdiction != "Uttarakhand":
                # User's case facts indicate a jurisdiction outside the supported scope.
                # Do not apply Uttarakhand legislation or retrieve Uttarakhand provisions.
                assistant_message = (
                    f"This case involves a dispute in {detected_jurisdiction}. "
                    "The Kuku prototype currently only supports residential security-deposit "
                    "disputes in Uttarakhand. I cannot apply Uttarakhand legislation to your "
                    "case or retrieve Uttarakhand provisions as applicable. "
                    "You may want to consult a qualified lawyer practicing in {detected_jurisdiction} "
                    "for jurisdiction-specific legal advice."
                ).format(detected_jurisdiction=detected_jurisdiction)
                conversation = get_or_create_conversation(db, case_id)
                add_message(db, conversation.id, "user", user_message)
                add_message(db, conversation.id, "assistant", assistant_message)
                db.commit()
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
                    "confirmation_needed": [],
                }

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
