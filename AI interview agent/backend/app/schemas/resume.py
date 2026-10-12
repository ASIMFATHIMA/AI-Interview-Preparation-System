from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class ResumeItem(BaseModel):
    """
    Compact resume metadata representation.
    """
    resume_id: int
    original_name: str
    file_type: str
    file_size: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class ResumeDetailResponse(BaseModel):
    """
    Detailed resume metadata response.
    """
    resume_id: int
    student_id: int
    original_name: str
    stored_name: str
    file_type: str
    file_size: int
    status: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResponse(BaseModel):
    """
    Response schema for basic resume upload endpoint (no parsed data).
    """
    success: bool = True
    message: str = "Resume uploaded successfully"
    resume: ResumeItem


class ResumeUploadWithParsedResponse(BaseModel):
    """
    Response schema for resume upload + parse endpoint.
    Includes both metadata and structured parsed data extracted from the resume.
    """
    success: bool = True
    message: str = "Resume uploaded and parsed successfully"
    candidate_id: int
    resume_id: int
    resume: ResumeItem
    parsed: Optional[Any] = None          # ParsedResumeData dict or None on parse failure
    parse_error: Optional[str] = None     # Human-readable error if parsing failed


class ResumeProfileResponse(BaseModel):
    candidate_id: int
    resume_id: int
    resume: ResumeDetailResponse
    profile: dict


class ResumeParseResponse(BaseModel):
    """
    Response schema for the re-parse endpoint.
    """
    success: bool = True
    message: str = "Resume re-parsed successfully"
    data: Optional[Any] = None


class ResumeDeleteResponse(BaseModel):
    """
    Response schema for resume deletion.
    """
    success: bool = True
    message: str = "Resume deleted successfully"
from pydantic import BaseModel
from typing import List, Any


class ResumeExtractionResponse(BaseModel):

    summary: str = ""

    skills: List[str] = []

    education: List[Any] = []

    experience: List[Any] = []

    projects: List[Any] = []

    certifications: List[Any] = []

    achievements: List[Any] = []