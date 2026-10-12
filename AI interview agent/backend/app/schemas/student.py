from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class StudentRegisterRequest(BaseModel):
    """
    Schema for student registration.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the student")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password with at least 8 characters")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class StudentLoginRequest(BaseModel):
    """
    Schema for student login.
    """
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Student account password")


class TokenResponse(BaseModel):
    """
    Schema for JWT token response.
    """
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    Decoded JWT token payload structure.
    """
    student_id: Optional[int] = None
    email: Optional[str] = None


class StudentResponse(BaseModel):
    """
    Safe public student response schema without password_hash.
    """
    student_id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    institution: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    parsed_resume: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentProfileUpdateRequest(BaseModel):
    """
    Schema for updating student profile details.
    Sensitive fields (student_id, password_hash, email, created_at) are excluded.
    """
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name of the student")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    location: Optional[str] = Field(None, max_length=100, description="City / Country / Location")
    degree: Optional[str] = Field(None, max_length=100, description="Degree name, e.g., B.Tech, M.S.")
    field_of_study: Optional[str] = Field(None, max_length=100, description="Field of study or major")
    institution: Optional[str] = Field(None, max_length=150, description="College or University name")
    github_url: Optional[str] = Field(None, max_length=255, description="GitHub profile URL")
    linkedin_url: Optional[str] = Field(None, max_length=255, description="LinkedIn profile URL")
    portfolio_url: Optional[str] = Field(None, max_length=255, description="Personal portfolio or website URL")

    model_config = ConfigDict(extra="forbid")
