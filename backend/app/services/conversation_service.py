from typing import Optional

from sqlalchemy.orm import Session

from app.database.models import Case, Conversation, Message
from app.schemas.conversation import MessageCreate


def get_or_create_conversation(db: Session, case_id: str) -> Conversation:
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    conversation = (
        db.query(Conversation).filter(Conversation.case_id == case_id).first()
    )
    if not conversation:
        conversation = Conversation(case_id=case_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation


def add_message(
    db: Session, conversation_id: str, role: str, content: str
) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages(db: Session, conversation_id: str) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )