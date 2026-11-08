from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Case
from app.schemas.case import CaseResponse, CaseUpdate

router = APIRouter(tags=["cases"])


@router.post("", response_model=CaseResponse, status_code=201)
def create_case_endpoint(db: Session = Depends(get_db)):
    from app.services.case_service import create_case

    case = create_case(db)
    return case


@router.get("/{case_id}", response_model=CaseResponse)
def get_case_endpoint(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case_endpoint(
    case_id: str, update: CaseUpdate, db: Session = Depends(get_db)
):
    from app.services.case_service import update_case

    case = update_case(db, case_id, update)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case