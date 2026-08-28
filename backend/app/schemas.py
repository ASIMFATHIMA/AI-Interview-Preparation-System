from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Student ----------

class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    created_at: datetime


# ---------- Resume ----------

class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    filename: str
    uploaded_at: datetime


# ---------- Structured extraction sub-objects ----------

class SkillItem(BaseModel):
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None


class EducationItem(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None


class ExperienceItem(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class ProjectItem(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[str] = None
    link: Optional[str] = None


class ExtractedResume(BaseModel):
    """Schema the LLM is instructed to return. Used to validate its JSON output."""

    summary: Optional[str] = None
    skills: List[SkillItem] = []
    education: List[EducationItem] = []
    experience: List[ExperienceItem] = []
    projects: List[ProjectItem] = []


# ---------- Candidate Profile (full, as returned by API) ----------

class CandidateProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    resume_id: Optional[int]
    summary: Optional[str]
    updated_at: datetime
    skills: List[SkillItem] = []
    education: List[EducationItem] = []
    experience: List[ExperienceItem] = []
    projects: List[ProjectItem] = []


class ParseResponse(BaseModel):
    resume_id: int
    profile: CandidateProfileOut
    raw_extraction: Any
