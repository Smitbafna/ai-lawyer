from typing import Optional, Dict, List, Any, Tuple

from sqlalchemy.orm import Session

from app.database.models import Case
from app.schemas.document import DocumentRequest, DocumentType
from fastapi import HTTPException


def _get_case(db: Session, case_id: str) -> Case:
    """Look up a case by ID; raises 404 if not found."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"Case {case_id} not found",
        )
    return case


class DocumentService:
    """
    Foundational document service that will eventually coordinate:

    1. Case fact loading.
    2. Document-specific requirements.
    3. Jurisdiction applicability.
    4. Legal source retrieval.
    5. Structured LLM generation.
    6. Deterministic validation.
    7. Document persistence.
    8. Export.
    """

    def __init__(self, db_session_factory):
        self._db_session_factory = db_session_factory

    def load_case_facts(self, case_id: str) -> dict[str, Any]:
        """
        Load existing case facts from the database.

        Returns the structured_facts dict from the case record.
        """
        from app.database.connection import SessionLocal

        db = self._db_session_factory()
        try:
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                return {}
            return case.structured_facts or {}
        finally:
            db.close()

    def check_document_requirements(
        self,
        case_id: str,
        document_type: DocumentType,
        user_instructions: str | None = None,
        additional_information: dict[str, Any] | None = None,
    ) -> DocumentRequirementsResponse:
        """
        Check whether the required information is available for a document type.

        This is a foundational method that will be expanded in D2/D3 to implement
        document-type-specific requirements analysis.
        """
        from app.database.connection import SessionLocal

        db = self._db_session_factory()
        try:
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise ValueError(f"Case {case_id} not found")

            structured_facts = case.structured_facts or {}

            # D1 placeholder: minimal requirements check
            blocking_reasons: List[str] = [
                "Document generation not yet implemented (D1 foundation only)",
            ]

            available_information: List[str] = [
                f"case_id={case_id}",
                f"case_type={case.case_type}",
            ]

            required_information: List[str] = [
                "user_instructions",
                "case_facts_analysis",
            ]

            # Extract any known fields from structured facts
            known_fields: List[str] = list(structured_facts.keys())
            missing_information: List[str] = [
                f for f in known_fields
            ] if structured_facts else []

            confirmation_required = False
            can_generate = False

            return DocumentRequirementsResponse(
                case_id=case_id,
                document_type=document_type,
                required_information=required_information,
                available_information=available_information,
                missing_information=missing_information,
                confirmation_required=confirmation_required,
                can_generate=can_generate,
                blocking_reasons=blocking_reasons,
            )
        finally:
            db.close()

    def validate_document_request(
        self,
        request: DocumentRequest,
    ) -> Tuple[Optional[Case], Optional[str]]:
        """
        Validate a document request.

        Returns (case, error_message) where error_message is None if valid,
        or an error string if the request is invalid.
        """
        from app.database.connection import SessionLocal

        db = self._db_session_factory()
        try:
            case = db.query(Case).filter(Case.id == request.case_id).first()
            if not case:
                return None, f"Case {request.case_id} not found"

            # Validate document type is supported
            # D1: All four document types are accepted but generation is not implemented
            # D2+: Will add jurisdiction and content-type specific validation

            return case, None
        finally:
            db.close()