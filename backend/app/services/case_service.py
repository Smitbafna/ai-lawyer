from typing import Optional

from sqlalchemy.orm import Session

from app.database.models import Case
from app.schemas.case import CaseUpdate, CaseResponse


def create_case(db: Session, case_type: str = "security_deposit_dispute") -> Case:
    case = Case(
        case_type=case_type,
        status="intake_in_progress",
        structured_facts={},
        missing_information=[],
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: str) -> Optional[Case]:
    return db.query(Case).filter(Case.id == case_id).first()


def update_case(db: Session, case_id: str, update: CaseUpdate) -> Optional[Case]:
    case = get_case(db, case_id)
    if not case:
        return None

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)
    return case


def update_case_facts(
    db: Session, case_id: str, structured_facts: dict, missing_information: list[str]
) -> Optional[Case]:
    case = get_case(db, case_id)
    if not case:
        return None

    case.structured_facts = structured_facts
    case.missing_information = missing_information
    db.commit()
    db.refresh(case)
    return case