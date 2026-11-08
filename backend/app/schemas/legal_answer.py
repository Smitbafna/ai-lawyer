from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LegalAnswer(BaseModel):
    """Structured legal answer with source grounding."""

    answer: str = Field(
        description="The legal answer or conclusion, grounded in the retrieved provisions.",
    )
    disposition: str = Field(
        description="One of: full_refund, partial_refund, over_cap_refund, abstain, clarify",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score based on grounding and provision support.",
    )
    cited_provisions: List[str] = Field(
        default_factory=list,
        description="Provision IDs that support the answer, e.g., ['ST-UK-11(1)', 'ST-UK-11(2)']",
    )
    source_reference: str = Field(
        description="Source reference, e.g., 'Uttarakhand Tenancy Act 2021, S 11(1)-(11(2)), SRC-02'",
    )
    explanation: str = Field(
        default="",
        description="Optional explanation of the reasoning, especially for clarifications and abstentions.",
    )
    unresolved_claims: List[str] = Field(
        default_factory=list,
        description="Unresolved claim IDs that affect the answer, if any.",
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
    )
    applicability: str = Field(
        default="uncertain",
        description="One of: applicable, not_applicable, uncertain. Whether the Uttarakhand Tenancy Act, 2021 applies to this case.",
    )
    applicability_reason: str = Field(
        default="",
        description="Explanation of why applicability is in this state, especially for not_applicable and uncertain.",
    )


class GroundingCheck(BaseModel):
    """Deterministic grounding check result."""

    well_grounded: bool = Field(
        description="Whether the answer is fully supported by the retrieved provisions.",
    )
    missing_support: List[str] = Field(
        default_factory=list,
        description="Provision IDs cited in the answer but not found in the retrieved context.",
    )
    unsupported_conclusions: List[str] = Field(
        default_factory=list,
        description="Conclusion statements that are not grounded in the provided provisions.",
    )
    abstention_required: bool = Field(
        description="Whether the answer requires abstention due to insufficient grounding.",
    )
    check_details: str = Field(
        description="Human-readable details of the grounding assessment.",
    )


class LegalAnswerRequest(BaseModel):
    """Request schema for legal answer generation.

    Note: jurisdiction is server-enforced as 'Uttarakhand' and must NOT be supplied by the client.
    case_facts are supplementary context from the intake workflow and must not override
    confirmed facts in the database.
    """

    case_id: str = Field(
        description="The case ID to associate the answer with.",
    )
    user_question: str = Field(
        description="The user's legal question.",
    )
    case_facts: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Supplementary case facts from the intake workflow. "
        "These are for context only and must not override confirmed facts in the database. "
        "Confirmed facts remain authoritative from the case record.",
    )
    retrieved_provisions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Provisions returned by hybrid_search(), already in context. "
        "Note: The service calls hybrid_search() fresh and overrides any client-supplied provisions.",
    )
    # jurisdiction field REMOVED - server-enforced as 'Uttarakhand' only


class LegalAnswerResponse(BaseModel):
    """Response schema for legal answer API endpoint."""

    case_id: str
    legal_answer: LegalAnswer
    grounding_check: GroundingCheck
    retrieval_metadata: Dict[str, Any] = Field(
        description="Metadata about the retrieval search (top_k, similarity scores, etc.).",
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)
