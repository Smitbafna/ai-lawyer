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

            def save_draft(self, case_id: str, document_type: DocumentType, content: str) -> Document:
            from app.database.connection import SessionLocal
            from datetime import datetime
            db = self._db_session_factory()
            try:
                case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise ValueError(f"Case {case_id} not found")
            existing = (
                db.query(Document)
                .filter(Document.case_id == case_id)
                .first()
            )
            if existing:
                previous_entry = {
                    "version": existing.version,
                    "content": existing.content,
                    "timestamp": existing.updated_at.isoformat() if existing.updated_at else None,
                }
                existing_previous = existing.previous_versions or []
                existing_previous.append(previous_entry)
                if len(existing_previous) > 10:
                    existing_previous = existing_previous[-10:]
                existing.previous_versions = existing_previous
                existing.version += 1
                existing.content = content
                existing.status = "draft_generated"
                existing.updated_at = datetime.utcnow()
                db.flush()
                return existing
            else:
                document = Document(
                    case_id=case_id,
                    document_type=document_type,
                    status="draft_generated",
                    content=content,
                    version=1,
                )
                db.add(document)
                db.flush()
                return document
        finally:
            db.close()

    def get_document(self, document_id: str) -> Optional[Document]:
        from app.database.connection import SessionLocal
        db = self._db_session_factory()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return None
            case = db.query(Case).filter(Case.id == document.case_id).first()
            if not case:
                return None
            return document
        finally:
            db.close()

    def save_edited_version(self, document_id: str, new_content: str) -> Document:
        from app.database.connection import SessionLocal
        from datetime import datetime
        db = self._db_session_factory()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")
            previous_entry = {
                "version": document.version,
                "content": document.content,
                "timestamp": document.updated_at.isoformat() if document.updated_at else None,
            }
            document_previous = document.previous_versions or []
            document_previous.append(previous_entry)
            document.previous_versions = document_previous
            document.version += 1
            document.content = new_content
            document.status = "draft_generated"
            document.updated_at = datetime.utcnow()
            db.flush()
            return document
        finally:
            db.close()

    def update_document_status(self, document_id: str, status: str) -> Document:
        from app.database.connection import SessionLocal
        from datetime import datetime
        db = self._db_session_factory()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")
            document.status = status
            document.updated_at = datetime.utcnow()
            db.flush()
            return document
        finally:
            db.close()