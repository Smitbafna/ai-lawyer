from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Jurisdiction(BaseModel):
    state: Optional[str] = None
    city: Optional[str] = None


class Parties(BaseModel):
    tenant: Optional[str] = None
    landlord: Optional[str] = None


class TimelineEvent(BaseModel):
    date: Optional[str] = None
    event: Optional[str] = None


class SecurityDepositDisputeFacts(BaseModel):
    case_type: str = "security_deposit_dispute"
    jurisdiction: Optional[Jurisdiction] = None
    parties: Optional[Parties] = None
    property_address: Optional[str] = None
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None
    vacating_date: Optional[date] = None
    security_deposit_amount: Optional[float] = None
    security_deposit_currency: Optional[str] = "INR"
    deposit_payment_date: Optional[date] = None
    deposit_payment_method: Optional[str] = None
    rental_agreement_exists: Optional[bool] = None
    refund_clause: Optional[str] = None
    landlord_response: Optional[str] = None
    facts: list[str] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    evidence_available: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class CaseUpdate(BaseModel):
    jurisdiction_state: Optional[str] = None
    jurisdiction_city: Optional[str] = None
    structured_facts: Optional[dict[str, Any]] = None
    missing_information: Optional[list[str]] = None
    status: Optional[str] = None


class CaseResponse(BaseModel):
    id: str
    case_type: str
    jurisdiction_state: Optional[str]
    jurisdiction_city: Optional[str]
    status: str
    structured_facts: Optional[dict[str, Any]]
    missing_information: Optional[list[str]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True