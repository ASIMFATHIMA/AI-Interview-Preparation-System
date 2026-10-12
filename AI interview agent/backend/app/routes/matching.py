import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import Student
from app.models.agents import JobMatch
from app.schemas.agents import MatchingHistoryItem, MatchingRequest, MatchingResult
from app.services.agent_services import analyze_match
from app.services.auth_service import get_current_student

router = APIRouter(prefix="/matching", tags=["Job-Resume Matching Agent"])


@router.post("/analyze", response_model=MatchingResult)
def analyze(data: MatchingRequest, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return analyze_match(db, current_student, data)


@router.get("/history", response_model=list[MatchingHistoryItem])
def history(current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    records = db.query(JobMatch).filter(JobMatch.student_id == current_student.student_id).order_by(JobMatch.created_at.desc()).all()
    return [{
        "match_id": item.match_id,
        "job_id": item.job_id,
        "match_score": item.match_score,
        "skill_score": item.skill_score,
        "experience_score": item.experience_score,
        "education_score": item.education_score,
        "project_score": item.project_score,
        "matched_skills": json.loads(item.matched_skills or "[]"),
        "missing_skills": json.loads(item.missing_skills or "[]"),
        "recommendation": item.recommendation,
        "explanation": item.explanation,
        "created_at": item.created_at,
    } for item in records]
