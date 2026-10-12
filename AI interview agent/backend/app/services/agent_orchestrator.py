"""Central routing boundary for authenticated career-agent requests."""

from sqlalchemy.orm import Session

from app.models.agents import SkillGapReport
from app.models.student import Student
from app.services.agent_services import _load, candidate_context


def route_request(db: Session, student: Student, message: str) -> tuple[str, str]:
    """Route a request using the candidate's verified profile context."""
    lower = message.lower()
    if any(word in lower for word in ("cover letter", "coverletter")):
        return "cover_letter", "I can generate a job-specific cover letter once you provide the job title, company, and description."
    if any(word in lower for word in ("interview", "mock interview", "practice")):
        return "interview", "I can start a tailored interview using your parsed resume and a target job description."
    if any(word in lower for word in ("match", "job", "apply")):
        return "job_resume_matching", "Use Job Matching with a job description to receive a transparent score and missing requirements."
    if any(word in lower for word in ("missing skill", "skill gap", "learn", "skill")):
        report = db.query(SkillGapReport).filter(SkillGapReport.student_id == student.student_id).order_by(SkillGapReport.created_at.desc()).first()
        if report:
            stored = _load(report.gaps, {})
            missing = stored.get("missing_skills", []) if isinstance(stored, dict) else []
            if missing:
                return "skill_gap", f"Your latest analysis prioritizes {', '.join(missing[:5])}. Start with the highest-priority gaps in the learning roadmap for {report.target_role or 'your target role'}."
        return "skill_gap", "Run Skill Gap Analysis with a target job to receive prioritized learning paths from your parsed resume."
    if any(word in lower for word in ("resume", "cv")):
        return "resume", "Your Resume Agent parses PDF/DOCX files and stores structured evidence in your candidate profile."

    context = candidate_context(db, student)
    top = ", ".join(context["skills"][:5]) or "your current profile"
    return "career_assistant", f"Based on your profile, start by strengthening {top}. Upload a resume and choose a target job for more specific recommendations."