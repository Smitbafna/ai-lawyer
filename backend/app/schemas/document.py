from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class DocumentType(str, Enum):
    legal_notice = "legal_notice"
    complaint = "complaint"
    reply = "reply"
    application = "application"


class DocumentRequest(BaseModel):
    """Schema for a document generation request."""

    case_id: str = Field(
        description="The case ID to associate the document with.",
    )
    document_type: DocumentType = Field(
        description="The type of document to prepare.",
    )
    user_instructions: Optional[str] = Field(
        default=None,
        description="Optional free-form instructions from the user about the document.",
        min_length=1,
    )
    additional_information: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional structured additional information (e.g., jurisdiction, parties, amounts).",
    )

    @validator("case_id")
    def validate_case_id(cls, v: str) -> str:
        """Validate that case_id is a proper UUID format."""
        import uuid

        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("Invalid case_id format: must be a valid UUID")
        return v

    @validator("user_instructions")
    def validate_instructions(cls, v: Optional[str]) -> Optional[str]:
        """Validate user instructions are not empty or excessively long."""
        if v is not None:
            stripped = v.strip()
            if stripped == "":
                raise ValueError("user_instructions must not be empty")
            if len(stripped) > 5000:
                raise ValueError("user_instructions must not exceed 5000 characters")
        return v

    @validator("document_type")
    def validate_document_type(cls, v: DocumentType) -> DocumentType:
        """Document type is validated by the enum, but ensure it's supported."""
        # The enum already restricts to supported types; no further check needed.
        return v


class DocumentRequirementsResponse(BaseModel):
    """Schema representing the information readiness check for a document request."""

    case_id: str
    document_type: DocumentType
    required_information: List[str]
    available_information: List[str]
    missing_information: List[str]
    confirmation_required: bool
    can_generate: bool
    blocking_reasons: List[str]


class DocumentResponse(BaseModel):
    """Common response schema for document API endpoints."""

    document_id: Optional[str] = Field(
        default=None,
        description="Document ID if a document was generated, otherwise None.",
    )
    case_id: str
    document_type: DocumentType
    status: str
    message: str
    blocking_reasons: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Status enum for document generation pipeline
class DocumentStatus(str, Enum):
    requirements_pending = "requirements_pending"
    blocked = "blocked"
    ready_for_generation = "ready_for_generation"
    draft_generated = "draft_generated"
    failed = "failed"