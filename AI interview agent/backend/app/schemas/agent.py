"""Shared contracts for the career-agent responsibilities."""
from enum import Enum
from typing import Tuple

from pydantic import BaseModel, Field


class AgentName(str, Enum):
    JOB_RESUME_MATCHING = "job_resume_matching"
    SKILL_GAP = "skill_gap"
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    INTERVIEW = "interview"
    CAREER_ASSISTANT = "career_assistant"


class AgentResponsibility(BaseModel):
    """Ownership contract used when routing work to a career agent."""

    name: AgentName
    purpose: str
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    owns: Tuple[str, ...]
    must_not_modify: Tuple[str, ...]


AGENT_RESPONSIBILITIES: Tuple[AgentResponsibility, ...] = (
    AgentResponsibility(
        name=AgentName.JOB_RESUME_MATCHING,
        purpose="Rank job opportunities against the candidate profile and resume evidence.",
        inputs=("candidate_profile", "parsed_resume", "job_description"),
        outputs=("match_score", "matching_skills", "missing_requirements", "match_explanation"),
        owns=("job_matches", "match_scores"),
        must_not_modify=("parsed_resume", "candidate_profile", "job_description"),
    ),
    AgentResponsibility(
        name=AgentName.SKILL_GAP,
        purpose="Compare target-role requirements with verified candidate skills and identify gaps.",
        inputs=("candidate_profile", "parsed_resume", "target_role", "job_description"),
        outputs=("skill_gaps", "priority", "learning_plan", "evidence"),
        owns=("skill_gap_reports", "learning_recommendations"),
        must_not_modify=("parsed_resume", "match_scores", "resume_content"),
    ),
    AgentResponsibility(
        name=AgentName.RESUME,
        purpose="Parse, normalize, tailor, and improve resume content without inventing evidence.",
        inputs=("resume_file", "parsed_resume", "target_role", "job_description"),
        outputs=("structured_resume", "resume_feedback", "tailored_resume"),
        owns=("resume_versions", "resume_feedback"),
        must_not_modify=("password_hash", "account_identity", "verified_profile_facts"),
    ),
    AgentResponsibility(
        name=AgentName.COVER_LETTER,
        purpose="Generate a truthful, job-specific cover letter from profile and resume evidence.",
        inputs=("candidate_profile", "parsed_resume", "job_description"),
        outputs=("cover_letter", "personalization_points", "unsupported_claim_warnings"),
        owns=("cover_letters",),
        must_not_modify=("parsed_resume", "candidate_profile", "job_description"),
    ),
    AgentResponsibility(
        name=AgentName.INTERVIEW,
        purpose="Prepare and conduct role-specific interview practice with actionable feedback.",
        inputs=("candidate_profile", "parsed_resume", "job_description", "skill_gap_report"),
        outputs=("questions", "model_answers", "feedback", "readiness_score"),
        owns=("interview_sessions", "interview_feedback"),
        must_not_modify=("parsed_resume", "match_scores", "verified_profile_facts"),
    ),
    AgentResponsibility(
        name=AgentName.CAREER_ASSISTANT,
        purpose="Coordinate career workflows and answer profile-aware career questions.",
        inputs=("candidate_profile", "agent_outputs", "user_request"),
        outputs=("recommendation", "next_action", "workflow_summary"),
        owns=("conversation_state", "workflow_tasks"),
        must_not_modify=("password_hash", "parsed_resume", "agent_source_records"),
    ),
)


def get_agent_responsibility(agent_name: AgentName) -> AgentResponsibility:
    """Return the ownership contract for one agent."""
    for responsibility in AGENT_RESPONSIBILITIES:
        if responsibility.name == agent_name:
            return responsibility
    raise ValueError(f"Unknown agent: {agent_name}")
