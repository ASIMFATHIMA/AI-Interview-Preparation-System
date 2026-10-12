from sqlalchemy.orm import Session
from app.models.student import Student
from app.schemas.student import StudentProfileUpdateRequest


def update_student_profile(
    db: Session,
    student: Student,
    profile_data: StudentProfileUpdateRequest,
) -> Student:
    """
    Updates the authenticated student's profile attributes safely.
    Only explicitly provided, non-sensitive fields from the update request are applied.
    """
    update_dict = profile_data.model_dump(exclude_unset=True)

    allowed_fields = {
        "name",
        "phone",
        "location",
        "degree",
        "field_of_study",
        "institution",
        "github_url",
        "linkedin_url",
        "portfolio_url",
    }

    for field, value in update_dict.items():
        if field in allowed_fields:
            if isinstance(value, str):
                value = value.strip()
            setattr(student, field, value)

    db.add(student)
    db.commit()
    db.refresh(student)
    return student
