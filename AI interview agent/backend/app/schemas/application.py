"""Pydantic contracts for the Application Tracking module (M4.1)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


APPLICATION_STATUSES = [
    "Saved",
    "Planning to Apply",
    "Applied",
    "Application Under Review",
    "Shortlisted",
    "Interview Scheduled",
    "Interview Completed",
    "Offer Received",
    "Rejected",
    "Withdrawn",
    "Interested",
    "Assessment",
    "Interview",
    "Selected",
]

INTERVIEW_STATUSES = [
    "Not Scheduled",
    "Scheduled",
    "Completed",
    "Rescheduled",
    "Cancelled",
]

INTERVIEW_OUTCOMES = [
    "Pending",
    "Passed",
    "Failed",
    "Selected",
    "Waiting for Result",
]


class ApplicationCreateRequest(BaseModel):
    """Request body for creating a new application record."""

    job_id: Optional[int] = Field(None, description="Internal job_id, if known")
    job_title: Optional[str] = Field(None, min_length=1, max_length=200, description="Job title")
    title: Optional[str] = Field(None, exclude=True)
    company: Optional[str] = Field(None, min_length=1, max_length=200, description="Company name")
    company_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Company name")
    job_description: Optional[str] = Field(None, description="Job description")
    description: Optional[str] = Field(None, exclude=True)
    location: Optional[str] = Field(None, max_length=150, description="Job location")
    application_date: Optional[datetime] = Field(None, description="Date the application was submitted")
    application_deadline: Optional[datetime] = Field(None, description="Application deadline")
    deadline: Optional[datetime] = Field(None, description="Application deadline")
    status: str = Field("Saved", description="Initial application status")
    interview_date: Optional[datetime] = Field(None, description="Interview date")
    interview_time: Optional[str] = Field(None, description="Interview time")
    interview_status: Optional[str] = Field("Not Scheduled", description="Interview status")
    interview_type: Optional[str] = Field(None, description="Interview type")
    interview_notes: Optional[str] = Field(None, description="Interview notes")
    interview_outcome: Optional[str] = Field("Pending", description="Interview outcome")
    notes: Optional[str] = Field(None, description="Free-form notes")
    follow_up_information: Optional[str] = Field(None, description="Follow-up details")
    next_follow_up_date: Optional[datetime] = Field(None, description="Next follow-up date")
    next_action: Optional[str] = Field(None, description="Next step to take")
    resume_id: Optional[int] = Field(None, description="Associated customized resume")
    cover_letter_id: Optional[int] = Field(None, description="Associated cover letter")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)

        company_name = normalized.get("company_name") or normalized.get("company")
        if company_name is not None:
            normalized["company_name"] = company_name
            normalized["company"] = company_name

        if "job_title" not in normalized and normalized.get("title"):
            normalized["job_title"] = normalized["title"]

        if "job_description" not in normalized and normalized.get("description"):
            normalized["job_description"] = normalized["description"]

        if "application_deadline" not in normalized and normalized.get("deadline"):
            normalized["application_deadline"] = normalized["deadline"]
        if "deadline" not in normalized and normalized.get("application_deadline"):
            normalized["deadline"] = normalized["application_deadline"]

        if normalized.get("status") is None:
            normalized["status"] = "Saved"
        return normalized


class ApplicationUpdateRequest(BaseModel):
    """Request body for updating an existing application record."""

    job_id: Optional[int] = None
    job_title: Optional[str] = Field(None, min_length=1, max_length=200)
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)
    job_description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=150)
    application_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = Field(None, description="New application status")
    interview_date: Optional[datetime] = None
    interview_time: Optional[str] = None
    interview_status: Optional[str] = None
    interview_type: Optional[str] = None
    interview_notes: Optional[str] = None
    interview_outcome: Optional[str] = None
    notes: Optional[str] = None
    follow_up_information: Optional[str] = None
    next_follow_up_date: Optional[datetime] = None
    next_action: Optional[str] = None
    resume_id: Optional[int] = None
    cover_letter_id: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)

        company_name = normalized.get("company_name") or normalized.get("company")
        if company_name is not None:
            normalized["company_name"] = company_name
            normalized["company"] = company_name

        if "application_deadline" not in normalized and normalized.get("deadline"):
            normalized["application_deadline"] = normalized["deadline"]
        if "deadline" not in normalized and normalized.get("application_deadline"):
            normalized["deadline"] = normalized["application_deadline"]

        return normalized


class ApplicationStatusUpdateRequest(BaseModel):
    """Request body for updating only the application status."""

    status: str = Field(..., description="New application status")


class ApplicationInterviewUpdateRequest(BaseModel):
    """Request body for updating interview information."""

    interview_date: Optional[datetime] = None
    interview_time: Optional[str] = None
    interview_status: Optional[str] = Field(None, description="Interview status")
    interview_type: Optional[str] = None
    interview_notes: Optional[str] = None
    interview_outcome: Optional[str] = None


class ApplicationNotesUpdateRequest(BaseModel):
    """Request body for updating notes and follow-up information."""

    notes: Optional[str] = None
    follow_up_information: Optional[str] = None
    next_follow_up_date: Optional[datetime] = None
    next_action: Optional[str] = None


class ApplicationOut(BaseModel):
    """Public application response schema."""

    application_id: int
    student_id: int
    job_id: Optional[int] = None
    job_title: str
    company: Optional[str] = None
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    application_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: str
    interview_date: Optional[datetime] = None
    interview_time: Optional[str] = None
    interview_status: Optional[str] = None
    interview_type: Optional[str] = None
    interview_notes: Optional[str] = None
    interview_outcome: Optional[str] = None
    notes: Optional[str] = None
    follow_up_information: Optional[str] = None
    next_follow_up_date: Optional[datetime] = None
    next_action: Optional[str] = None
    resume_id: Optional[int] = None
    cover_letter_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationListResponse(BaseModel):
    """List response for applications."""

    total: int
    applications: List[ApplicationOut]


class ApplicationStatsResponse(BaseModel):
    """Dashboard summary statistics for applications."""

    total: int = 0
    saved: int = 0
    interested: int = 0
    applied: int = 0
    assessment: int = 0
    interview: int = 0
    selected: int = 0
    rejected: int = 0
    withdrawn: int = 0
    active: int = 0
    upcoming_deadlines: List[ApplicationOut] = Field(default_factory=list)
    interviews_scheduled: int = 0
    offers_received: int = 0
    pending_applications: int = 0
    upcoming_deadlines_count: int = 0