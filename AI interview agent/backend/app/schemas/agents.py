"""API contracts for jobs and career-agent workflows."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class JobCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    company: str = Field(..., min_length=1, max_length=200)
    location: Optional[str] = None
    experience: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    education_requirements: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    description: str = Field(..., min_length=10)


class JobOut(JobCreate):
    job_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MatchingRequest(BaseModel):
    job_id: Optional[int] = None
    job: Optional[JobCreate] = None
    skill_weight: float = Field(0.50, ge=0, le=1)
    experience_weight: float = Field(0.20, ge=0, le=1)
    education_weight: float = Field(0.15, ge=0, le=1)
    project_weight: float = Field(0.15, ge=0, le=1)


class MatchingResult(BaseModel):
    match_id: Optional[int] = None
    job_id: Optional[int] = None
    match_score: int
    skill_score: int
    experience_score: int
    education_score: int
    project_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    recommendation: str
    explanation: str


class MatchingHistoryItem(MatchingResult):
    created_at: datetime


class SkillGapRequest(BaseModel):
    job_id: Optional[int] = None
    student_id: Optional[int] = None
    job_title: Optional[str] = Field(None, min_length=2, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    job_description: Optional[str] = Field(None, min_length=10)
    target_role: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)


class SkillGapItem(BaseModel):
    skill: str
    requirement_type: str = "Required"
    status: str = "missing"
    priority: str = "High"
    current_level: str = "Beginner"
    required_level: str = "Intermediate"
    why_it_matters: str = ""
    reason: str = ""
    recommended_action: str = ""
    recommendation: str = ""
    suggested_topic_project: str = ""
    project_recommendation: str = ""
    learning_path: List[str] = Field(default_factory=list)
    gap_description: str = ""
    estimated_difficulty: str = "Medium"


class SkillGapResult(BaseModel):
    report_id: Optional[int] = None
    target_role: Optional[str] = None
    current_skills: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    skill_gaps: List[SkillGapItem] = Field(default_factory=list)
    success: bool = True
    candidate_id: Optional[int] = None
    job_id: Optional[int] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    skill_match_score: int = 0
    skill_gap_score: int = 100
    matching_skills: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    partial_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    preferred_missing_skills: List[str] = Field(default_factory=list)
    experience_gaps: List[str] = Field(default_factory=list)
    qualification_gaps: List[str] = Field(default_factory=list)
    project_gaps: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    learning_roadmap: List[dict] = Field(default_factory=list)


class SkillGapHistoryItem(SkillGapResult):
    created_at: datetime


class ResumeCustomizeRequest(BaseModel):
    job_id: Optional[int] = None
    student_id: Optional[int] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    job_description: Optional[str] = None


class ResumeCustomizeResponse(BaseModel):
    job_title: str
    company: str
    tailored_resume: str
    keywords_used: List[str] = Field(default_factory=list)
    relevant_skills: List[str] = Field(default_factory=list)
    tailored_resume_id: Optional[int] = None
    created_at: Optional[datetime] = None
    success: bool = True


class ResumeCustomizeHistoryItem(ResumeCustomizeResponse):
    pass


class CoverLetterRequest(BaseModel):
    job_id: Optional[int] = None
    student_id: Optional[int] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    resume_text: Optional[str] = None
    additional_instructions: Optional[str] = ""


class CoverLetterOut(BaseModel):
    cover_letter_id: Optional[int] = None
    job_id: Optional[int] = None
    job_title: str = ""
    company: str = ""
    cover_letter: str = ""
    created_at: Optional[datetime] = None
    success: bool = True


class CoverLetterResponse(CoverLetterOut):
    pass


class CareerChatHistoryItem(BaseModel):
    chat_id: int
    message: str
    response: str
    routed_agent: str
    created_at: datetime


class InterviewQuestionItem(BaseModel):
    question: str
    category: str
    difficulty: str = "Medium"
    why_this_question_matters: str = ""
    preparation_guidance: str = ""


class InterviewPrepRequest(BaseModel):
    job_id: Optional[int] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    job_description: Optional[str] = None


class InterviewPrepResponse(BaseModel):
    job_title: str
    company: str
    questions: List[InterviewQuestionItem] = Field(default_factory=list)
    technical_questions: List[InterviewQuestionItem] = Field(default_factory=list)
    resume_questions: List[InterviewQuestionItem] = Field(default_factory=list)
    project_questions: List[InterviewQuestionItem] = Field(default_factory=list)
    role_questions: List[InterviewQuestionItem] = Field(default_factory=list)
    hr_questions: List[InterviewQuestionItem] = Field(default_factory=list)


class InterviewStartRequest(BaseModel):
    job_id: Optional[int] = None
    job_description: Optional[str] = None
    interview_type: str = Field("technical", pattern="^(technical|behavioral|hr|project|role-specific|job-specific|mixed)$")
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    question_count: int = Field(5, ge=1, le=20)


class InterviewStartResponse(BaseModel):
    interview_id: int
    status: str
    question_number: int
    total_questions: int
    question: str
    category: str


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=10000)


class InterviewAnswerResponse(BaseModel):
    interview_id: int
    question_number: int
    score: int
    feedback: str
    relevance: Optional[str] = None
    technical_correctness: Optional[str] = None
    completeness: Optional[str] = None
    communication: Optional[str] = None
    missing_points: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    next_question_available: bool


class InterviewResult(BaseModel):
    interview_id: int
    status: str
    overall_score: Optional[int] = None
    technical_score: Optional[int] = None
    communication_score: Optional[int] = None
    questions_answered: Optional[int] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    areas_to_improve: List[str] = Field(default_factory=list)
    technical_topics_to_revise: List[str] = Field(default_factory=list)
    project_topics_to_revise: List[str] = Field(default_factory=list)
    hr_preparation: List[str] = Field(default_factory=list)
    recommended_preparation_plan: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    report: Optional[dict] = None


class InterviewDetail(InterviewResult):
    interview_type: str
    difficulty: str
    question_count: int
    current_question: int
    created_at: datetime


class InterviewHistoryItem(InterviewDetail):
    pass


class CareerChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    student_id: Optional[int] = None
    job_id: Optional[int] = None


class CareerChatResponse(BaseModel):
    chat_id: Optional[int] = None
    routed_agent: str = "career_assistant"
    response: str
    context_used: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

