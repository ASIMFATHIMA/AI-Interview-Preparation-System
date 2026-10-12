from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import Student
from app.schemas.student import StudentResponse, StudentProfileUpdateRequest
from app.services.auth_service import get_current_student
from app.services.profile_service import update_student_profile
from app.services.resume_parser import get_parsed_data

router = APIRouter(
    prefix="/profile",
    tags=["Student Profile"],
)


@router.get(
    "/me",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current student profile",
    description="Retrieves the profile of the currently authenticated student using their JWT bearer token.",
)
def get_my_profile(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Returns only the authenticated student's profile details.
    """
    return {
        "student_id": current_student.student_id,
        "name": current_student.name,
        "email": current_student.email,
        "phone": current_student.phone,
        "location": current_student.location,
        "degree": current_student.degree,
        "field_of_study": current_student.field_of_study,
        "institution": current_student.institution,
        "github_url": current_student.github_url,
        "linkedin_url": current_student.linkedin_url,
        "portfolio_url": current_student.portfolio_url,
        "created_at": current_student.created_at,
        "updated_at": current_student.updated_at,
        "parsed_resume": {
            "name": current_student.name,
            "email": current_student.parsed_resume_email or current_student.email,
            "phone": current_student.phone,
            "location": current_student.location,
            "linkedin_url": current_student.linkedin_url,
            "github_url": current_student.github_url,
            "portfolio_url": current_student.portfolio_url,
            **get_parsed_data(db=db, student_id=current_student.student_id),
        },
    }


@router.put(
    "/me",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current student profile",
    description="Updates the profile of the currently authenticated student. Only allowed profile fields can be modified.",
)
def update_my_profile(
    profile_data: StudentProfileUpdateRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Updates profile fields for the authenticated student.
    - Uses JWT identity exclusively (no frontend-supplied student_id).
    - Prevents modification of sensitive fields like student_id, password_hash, created_at, or email.
    """
    updated_student = update_student_profile(
        db=db,
        student=current_student,
        profile_data=profile_data,
    )
    return updated_student
