from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import Student
from app.schemas.resume_parsed import ParsedResumeResponse
from app.services.auth_service import get_current_student
from app.services.resume_parser import get_parsed_data

router = APIRouter(
    prefix="/resume-parsed",
    tags=["Resume Parsed Data"],
)


@router.get(
    "/me",
    response_model=ParsedResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get parsed resume data for current student",
    description="Retrieves structured parsed resume data (skills, education, experience, etc.) for the authenticated student.",
)
def get_my_parsed_resume(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Returns all parsed resume data for the authenticated student.
    """
    parsed = get_parsed_data(db=db, student_id=current_student.student_id)
    return {
        "success": True,
        "message": "Parsed resume data retrieved successfully",
        "data": {
            "name": current_student.name,
            "email": current_student.parsed_resume_email or current_student.email,
            "phone": current_student.phone,
            "location": current_student.location,
            "linkedin_url": current_student.linkedin_url,
            "github_url": current_student.github_url,
            "portfolio_url": current_student.portfolio_url,
            "skills": parsed.get('skills', []),
            "education": parsed.get('education', []),
            "experience": parsed.get('experience', []),
            "projects": parsed.get('projects', []),
            "certifications": parsed.get('certifications', []),
            "achievements": parsed.get('achievements', []),
        },
    }
