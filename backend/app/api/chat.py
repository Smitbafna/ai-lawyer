from fastapi import APIRouter, Depends, HTTPException, status
import logging

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.api.deps import get_intake_workflow
from app.database.connection import get_db
from app.database.models import Case, Conversation, Message
from app.llm.provider import LLMProviderError
from app.schemas.conversation import ChatRequest, ChatResponse

router = APIRouter(prefix="/cases", tags=["chat"])


@router.post("/{case_id}/chat", response_model=ChatResponse)
async def chat_endpoint(
    case_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db),
    workflow: IntakeWorkflow = Depends(get_intake_workflow),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        result = await workflow.process_message(case_id, request.message, db)
    except ValueError as exc:
        if "version mismatch" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            )
        raise HTTPException(status_code=400, detail=str(exc))
    except LLMProviderError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return ChatResponse(
        assistant_message=result["assistant_message"],
        updated_case=result["updated_case"],
        missing_information=result["missing_information"],
        intake_status=result["intake_status"],
        confirmation_needed=result.get("confirmation_needed", []),
    )


@router.get("/{case_id}/messages")
def get_messages_endpoint(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    conversation = (
        db.query(Conversation).filter(Conversation.case_id == case_id).first()
    )
    if not conversation:
        return []

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": str(m.created_at) if m.created_at else None,
        }
        for m in messages
    ]