from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Case
from app.schemas.document import (
    DocumentRequest,
    DocumentRequirementsResponse,
    DocumentResponse,
    DocumentType,
    DocumentStatus,
)

router = APIRouter(tags=["documents"])


def _get_case(db: Session, case_id: str) -> Case:
    """Look up a case by ID; raises 404 if not found."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )
    return case


@router.post(
    "/requirements",
    response_model=DocumentRequirementsResponse,
    status_code=200,
    summary="Validate document request and check information readiness",
)
def document_requirements(
    request: DocumentRequest,
    db: Session = Depends(get_db),
):
    """
    Validate the document request, verify the case exists, load existing case facts,
    and determine whether the requested document type is supported by the current workflow.

    Returns an initial requirements response indicating what information is available,
    what's missing, and whether document generation can proceed.
    """
    # Verify case exists
    case = _get_case(db, request.case_id)

    # TODO: In D2, implement actual requirements engine that analyzes case facts
    # against document-type-specific requirements. For D1, return a placeholder
    # response that clearly identifies the current limitations.

    # For D1, we minimally check case existence and document type support.
    # The requirements engine returns a clearly identified placeholder response,
    # but does not pretend that missing information has been fully analyzed.

    # Determine blocking reasons - in D1, document generation is not yet implemented
    blocking_reasons: List[str] = [
        "Document generation not yet implemented (D1 foundation only)",
    ]

    # Available information from the case (basic facts)
    structured_facts = case.structured_facts or {}
    missing_information: List[str] = []
    if structured_facts:
        # Extract known fields from structured facts
        known_fields = list(structured_facts.keys())
        missing_information = [f for f in known_fields]

    required_information: List[str] = [
        "user_instructions",
        "case_facts_analysis",
    ]

    available_information: List[str] = [
        f"case_id={request.case_id}",
        f"case_type={case.case_type}",
    ]

    # For D1, confirmation is not required and generation is not possible
    confirmation_required = False
    can_generate = False

    return DocumentRequirementsResponse(
        case_id=request.case_id,
        document_type=request.document_type,
        required_information=required_information,
        available_information=available_information,
        missing_information=missing_information,
        confirmation_required=confirmation_required,
        can_generate=can_generate,
        blocking_reasons=blocking_reasons,
    )


@router.post(
    "/generate",
    response_model=DocumentResponse,
    status_code=200,
    summary="Generate a document (D1: returns 501 Not Implemented)",
)
def document_generate(
    request: DocumentRequest,
    db: Session = Depends(get_db),
):
    """
    Document generation endpoint.

    D1: Establish the endpoint and request validation.
    Return a controlled 501 Not Implemented response.
    Clearly explain that document generation has not yet been implemented.
    Never call Gemini to generate a document.
    Never return a successful document-generation status.

    In D1, this endpoint must:
    - Validate the request (case exists, document type supported)
    - Return a 501 status with clear explanation
    - Never persist a fake document record
    - Never call any LLM for generation
    """
    # Verify case exists
    case = _get_case(db, request.case_id)

    # D1: Document generation is not implemented.
    # Return a 501 Not Implemented response with clear explanation.
    # Never call Gemini to generate a document.
    # Never persist a fake document record.

    blocking_reasons: List[str] = [
        "Document generation not yet implemented. This endpoint is reserved for D2+ "
        "after the document generation pipeline has been audited and implemented.",
    ]

    # Use the DocumentStatus.failed to indicate generation did not occur
    response = DocumentResponse(
        document_id=None,
        case_id=request.case_id,
        document_type=request.document_type,
        status=DocumentStatus.failed,
        message="Document generation has not been implemented yet. "
        "This is a D1 foundation milestone; actual generation will be available in D2.",
        blocking_reasons=blocking_reasons,
    )

    # Raise 501 Not Implemented as specified in the requirements
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "document_id": None,
            "case_id": request.case_id,
            "document_type": request.document_type,
            "status": DocumentStatus.failed,
            "message": "Document generation not yet implemented. "
            "This endpoint is reserved for D2+ after the document generation pipeline "
            "has been audited and implemented.",
            "blocking_reasons": blocking_reasons,
        },
    )