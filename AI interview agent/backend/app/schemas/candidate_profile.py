"""Canonical candidate context shared by the career agents."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.resume_parsed import (
    EducationOut,
    ExperienceOut,
    ProjectOut,
    CertificationOut,
)


class CandidatePreferences(BaseModel):
    """Optional user-provided career preferences used for matching."""

    target_roles: List[str] = Field(default_factory=list)
    target_industries: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    preferred_work_modes: List[str] = Field(default_factory=list)
    target_companies: List[str] = Field(default_factory=list)
    work_authorization: Optional[str] = None


class CandidateProfileContext(BaseModel):
    """Read-only context passed to agents; it contains no credentials or secrets."""

    student_id: int
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    institution: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: List[EducationOut] = Field(default_factory=list)
    experience: List[ExperienceOut] = Field(default_factory=list)
    projects: List[ProjectOut] = Field(default_factory=list)
    certifications: List[CertificationOut] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    preferences: CandidatePreferences = Field(default_factory=CandidatePreferences)
    resume_updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")
