from fastapi import APIRouter, Depends, HTTPException, status

from app.database.connection import get_db as get_db_dep
from app.database.models import Case
from app.schemas.legal_answer import (
    LegalAnswerRequest,
    LegalAnswerResponse,
)
from app.services.legal_answer import LegalAnswerService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/legal-answer", tags=["legal-answer"])


def _get_service() -> LegalAnswerService:
    return LegalAnswerService()


@router.post(
    "",
    response_model=LegalAnswerResponse,
    status_code=200,
    summary="Generate a legal answer with Gemini + RAG grounding",
)
async def generate_legal_answer(
    request: LegalAnswerRequest,
    db: Session = Depends(get_db_dep),
    service: LegalAnswerService = Depends(_get_service),
):
    """Generate a source-grounded legal answer using Gemini and hybrid retrieval.

    The jurisdiction is server-enforced as 'Uttarakhand'. The API rejects
    requests that attempt to override jurisdiction via the schema
    (the LegalAnswerRequest no longer includes a client-supplied jurisdiction field).

    Takes the user's legal question, retrieves relevant provisions via
    hybrid_search() (fixed to Uttarakhand jurisdiction), passes context to Gemini,
    and validates grounding deterministically. Unsupported conclusions
    result in abstention.
    """
    # Validate case exists
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {request.case_id} not found",
        )

    result = await service.generate_legal_answer(
        case_id=request.case_id,
        user_question=request.user_question,
        case_facts=request.case_facts,
    )

    return result
