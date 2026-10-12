from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import Student
from app.models.agents import SkillGapReport
from app.schemas.agents import SkillGapHistoryItem, SkillGapRequest, SkillGapResult
from app.services.agent_services import _load
from app.services.agent_services import analyze_skill_gap
from app.services.auth_service import get_current_student

router = APIRouter(prefix="/skill-gap", tags=["Skill Gap Agent"])


@router.post("/analyze", response_model=SkillGapResult)
def analyze(data: SkillGapRequest, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return analyze_skill_gap(db, current_student, data)


@router.get("/history", response_model=list[SkillGapHistoryItem])
def history(current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    records = db.query(SkillGapReport).filter(SkillGapReport.student_id == current_student.student_id).order_by(SkillGapReport.created_at.desc()).all()
    results = []
    for item in records:
        stored = _load(item.gaps, {})
        if isinstance(stored, list):
            stored = {"skill_gaps": stored, "current_skills": [], "required_skills": []}
        results.append({
            "success": True,
            "report_id": item.report_id,
            "candidate_id": item.student_id,
            "job_id": item.job_id,
            "job_title": item.target_role,
            "target_role": item.target_role,
            "created_at": item.created_at,
            **stored,
        })
    return results
