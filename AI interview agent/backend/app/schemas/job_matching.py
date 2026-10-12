"""Contracts for M2 job retrieval and resume matching."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class JobSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(5, ge=1, le=25)


class JobSearchResult(BaseModel):
    job_id: str
    job_title: str
    company: str
    location: Optional[str] = None
    work_mode: Optional[str] = None
    job_type: Optional[str] = None
    similarity_score: float
    matched_sections: List[str]


class JobSearchResponse(BaseModel):
    query: str
    results: List[JobSearchResult]


class ResumeMatchRequest(BaseModel):
    student_id: Optional[int] = None
    top_k: int = Field(10, ge=1, le=25)


class ResumeMatchResult(JobSearchResult):
    match_score: float
    matched_skills: List[str]
    missing_required_skills: List[str]
    matched_preferred_skills: List[str]
    missing_preferred_skills: List[str]
    education_match: bool
    experience_match: bool
    project_match: bool
    reasoning: str
    recommendation: str
    description: str
    responsibilities: List[str]
    required_skills: List[str]
    preferred_skills: List[str]
    education_requirements: Optional[str] = None
    experience_requirements: Optional[str] = None
    qualifications: Optional[str] = None
    component_scores: Optional[Dict[str, float]] = None


class ResumeMatchResponse(BaseModel):
    student_id: int
    total_jobs_retrieved: int
    matches: List[ResumeMatchResult]
