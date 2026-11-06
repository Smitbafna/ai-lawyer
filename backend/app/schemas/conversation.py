from typing import Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    role: str
    content: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: Optional[str]

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    assistant_message: str
    updated_case: dict
    missing_information: list[str]
    intake_status: str
    confirmation_needed: list[str] = Field(default_factory=list)