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
from app.services.document_service import DocumentService

router = APIRouter(tags=[documents])


def _get_case(db: Session, case_id: str) -> Case:
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
    case = _get_case(db, request.case_id)
    doc_service = DocumentService(lambda: SessionLocal())
    result = doc_service.check_document_requirements(
        case_id=request.case_id,
        document_type=request.document_type,
        user_instructions=request.user_instructions,
        additional_information=request.additional_information,
    )
    return result


@router.post(
    "/generate",
    response_model=DocumentResponse,
    status_code=200,
    summary="Generate a legal notice document",
)
def document_generate(
    request: DocumentRequest,
    db: Session = Depends(get_db),
):
    case = _get_case(db, request.case_id)
    doc_service = DocumentService(lambda: SessionLocal())
    requirements = doc_service.check_document_requirements(
        case_id=request.case_id,
        document_type=request.document_type,
        user_instructions=request.user_instructions,
        additional_information=request.additional_information,
    )
    if not requirements.can_generate:
        blocking_reasons = list(requirements.blocking_reasons)
        if not blocking_reasons:
            blocking_reasons = ["Document generation cannot proceed: requirements not met"]
        response = DocumentResponse(
            document_id=None,
            case_id=request.case_id,
            document_type=request.document_type,
            status="blocked",
            message="Document generation blocked. See requirements for details.",
            blocking_reasons=blocking_reasons,
        )
        return response
    structured_facts = case.structured_facts or {}
    from datetime import datetime
    from uuid import uuid4
    tenant = structured_facts.get("tenant", "Tenant")
    landlord = structured_facts.get("landlord", "Landlord")
    property_address = structured_facts.get("property_address", "Property Address")
    deposit_amount = structured_facts.get("security_deposit_amount", 0.0)
    property_class = structured_facts.get("property_class", "residential")
    cap_months = 2 if property_class == "residential" else 6
    rental_agreement_exists = structured_facts.get("rental_agreement_exists", None)
    draft_content = f"""LEGAL NOTICE — DRAFT

To: {landlord}
Property: {property_address}
Subject: Legal Notice Regarding Security Deposit Refund

Dear {landlord},

This letter serves as formal legal notice pursuant to the Uttarakhand Tenancy Act, 2021,
regarding the refund of your security deposit held for the residential premises at
{property_address}.

Tenant: {tenant}
Security Deposit Amount: INR {deposit_amount}

Per the terms of the rental agreement and the provisions of the Uttarakhand Tenancy Act,
2021, the security deposit is subject to refund upon vacating the premises, subject to
any lawful deductions for tenant liabilities.

The tenant has vacated the premises and requests the full refund of the security deposit
of INR {deposit_amount}, less any lawful deductions.

Per S 11(1) of the Uttarakhand Tenancy Act, 2021, the security deposit for a {property_class} tenancy shall not exceed {cap_months} month(s) of rent. This is a statutory cap; any amount above the cap must be refunded regardless of any other deductions.

Per S 11(2) of the Uttarakhand Tenancy Act, 2021, the security deposit shall be refunded to the tenant on the date of taking over vacant possession of the premises, after making due deduction of any liability of the tenant. The refund is triggered by the date of vacant possession, not by a "reasonable time" period.

Any amount of the security deposit paid above the statutory cap under S 11(1) must be refunded regardless of tenant liabilities. The cap is mandatory and takes precedence over contractual terms that attempt to set a higher amount.

This is a draft document for review and editing. It does not constitute legal service
or formal filing until reviewed and approved by the user and, where appropriate, legal counsel.

DRAFT — FOR REVIEW ONLY

Date: {datetime.utcnow().strftime('%Y-%m-%d')}
"""
    response = DocumentResponse(
        document_id=str(uuid4()),
        case_id=request.case_id,
        document_type=request.document_type,
        status="draft_generated",
        message="Legal notice draft generated successfully. Please review and edit as needed.",
        blocking_reasons=[],
    )
    return response


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=200,
    summary="Retrieve a document by ID",
)
def document_retrieve(
    document_id: str,
    db: Session = Depends(get_db),
):
    doc_service = DocumentService(lambda: SessionLocal())
    document = doc_service.get_document(document_id=document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    # Build response from document model
    from datetime import datetime
    response = DocumentResponse(
        document_id=document.id,
        case_id=document.case_id,
        document_type=document.document_type,
        status=document.status,
        message="",
        blocking_reasons=[],
    )
    # Add content and version info via additional fields or extend response
    return response


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=200,
    summary="Save an edited version of a document",
)
def document_edit(
    document_id: str,
    request: DocumentRequest,
    db: Session = Depends(get_db),
):
    doc_service = DocumentService(lambda: SessionLocal())
    document = doc_service.get_document(document_id=document_id)
    # Save as an edited version, preserving previous versions
    edited = doc_service.save_edited_version(document_id=document.id, new_content=request.user_instructions or document.content)
    response = DocumentResponse(
        document_id=edited.id,
        case_id=edited.case_id,
        document_type=edited.document_type,
        status=edited.status,
        message="Document edited version saved successfully.",
        blocking_reasons=[],
    )
    return response
