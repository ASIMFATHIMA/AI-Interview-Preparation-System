from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SkillOut(BaseModel):
    id: int
    skill: str

    model_config = ConfigDict(from_attributes=True)


class EducationOut(BaseModel):
    id: int
    degree: Optional[str]
    institution: Optional[str]
    start_year: Optional[str]
    end_year: Optional[str]
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ExperienceOut(BaseModel):
    id: int
    company: Optional[str]
    role: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ProjectOut(BaseModel):
    id: int
    project_name: Optional[str]
    technologies: Optional[str]
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class CertificationOut(BaseModel):
    id: int
    certification_name: Optional[str]
    organization: Optional[str]
    year: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class AchievementOut(BaseModel):
    id: int
    achievement: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ParsedResumeData(BaseModel):
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: List[str]
    education: List[dict]
    experience: List[dict]
    projects: List[dict]
    certifications: List[dict]
    achievements: List[str]


class ParsedResumeResponse(BaseModel):
    success: bool = True
    message: str = "Resume parsed successfully"
    data: ParsedResumeData
