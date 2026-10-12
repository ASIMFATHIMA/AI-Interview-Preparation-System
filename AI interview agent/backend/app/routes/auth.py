from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import Student
from app.schemas.student import (
    StudentRegisterRequest,
    StudentLoginRequest,
    StudentResponse,
    TokenResponse,
)
from app.services.auth_service import (
    authenticate_student,
    create_access_token,
    get_current_student,
    register_student,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student",
    description="Registers a new student account, verifies email uniqueness, and securely stores password hash.",
)
def register(
    student_data: StudentRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Registers a new student.
    - Validates email and password requirements
    - Rejects duplicate email registrations
    - Returns safe public student profile (without password_hash)
    """
    new_student = register_student(db=db, student_data=student_data)
    return new_student


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Student login",
    description="Authenticates student with email and password, returning a signed JWT bearer access token.",
)
def login(
    login_data: StudentLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticates a student and issues a JWT token.
    """
    student = authenticate_student(db=db, login_data=login_data)

    access_token = create_access_token(
        data={
            "sub": student.email,
            "student_id": student.student_id,
            "name": student.name,
        }
    )
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated student profile",
    description="Retrieves the profile of the currently logged-in student using their Bearer JWT token.",
)
def get_me(
    current_student: Student = Depends(get_current_student),
):
    """
    Verifies JWT token and returns currently authenticated student profile.
    """
    return current_student
