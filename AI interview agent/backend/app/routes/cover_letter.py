from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import Student
from app.models.agents import CoverLetter
from app.schemas.agents import CoverLetterRequest, CoverLetterOut, CoverLetterResponse
from app.services.agent_services import generate_cover_letter as service_generate_cover_letter
from app.services.auth_service import get_current_student

router = APIRouter(
    prefix="/cover-letter",
    tags=["Cover Letter Agent"],
)


@router.post("/generate", response_model=CoverLetterOut)
def generate(
    request: CoverLetterRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return service_generate_cover_letter(db, current_student, request)


@router.post("/regenerate", response_model=CoverLetterOut)
def regenerate(
    request: CoverLetterRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return service_generate_cover_letter(db, current_student, request)


@router.get("", response_model=List[CoverLetterOut])
def list_cover_letters(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    records = (
        db.query(CoverLetter)
        .filter(CoverLetter.student_id == current_student.student_id)
        .order_by(CoverLetter.created_at.desc())
        .all()
    )
    return [
        {
            "cover_letter_id": item.cover_letter_id,
            "job_id": item.job_id,
            "job_title": item.job_title,
            "company": item.company,
            "cover_letter": item.content,
            "created_at": item.created_at,
            "success": True,
        }
        for item in records
    ]


@router.get("/{cover_letter_id}", response_model=CoverLetterOut)
def get_cover_letter(
    cover_letter_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    record = (
        db.query(CoverLetter)
        .filter(
            CoverLetter.cover_letter_id == cover_letter_id,
            CoverLetter.student_id == current_student.student_id,
        )
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cover letter not found.",
        )
    return {
        "cover_letter_id": record.cover_letter_id,
        "job_id": record.job_id,
        "job_title": record.job_title,
        "company": record.company,
        "cover_letter": record.content,
        "created_at": record.created_at,
        "success": True,
    }