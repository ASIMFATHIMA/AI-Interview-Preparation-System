from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import Student
from app.schemas.agents import JobCreate, JobOut
from app.services.agent_services import create_job, job_to_dict
from app.services.auth_service import get_current_student
from app.models.agents import Job
from app.schemas.job_matching import (
    JobSearchRequest,
    JobSearchResponse,
    JobSearchResult,
    ResumeMatchRequest,
    ResumeMatchResponse,
    ResumeMatchResult,
)
from app.services.candidate_query_builder import build_candidate_query
from app.services.job_matcher import calculate_match
from app.services.matching_reasoner import generate_matching_reasoning
from app.services.resume_parser import get_parsed_data
from app.services.vector_store import search_jobs

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=List[JobOut])
def list_jobs(_: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return [job_to_dict(job) for job in db.query(Job).order_by(Job.created_at.desc()).all()]


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def add_job(data: JobCreate, _: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return job_to_dict(create_job(db, data))


def _knowledge_job(db, dataset_job_id):
    return db.query(Job).filter(Job.dataset_job_id == dataset_job_id).first()


@router.post("/search", response_model=JobSearchResponse)
def search_knowledge_base(data: JobSearchRequest, _: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    hits = search_jobs(data.query, data.top_k)
    results = []
    for hit in hits:
        job = _knowledge_job(db, hit["job_id"])
        if not job:
            continue
        results.append({
            "job_id": job.dataset_job_id,
            "job_title": job.title,
            "company": job.company,
            "location": job.location,
            "work_mode": job.work_mode,
            "job_type": job.job_type,
            "similarity_score": round(hit["similarity_score"], 4),
            "matched_sections": hit["matched_sections"],
        })
    return {"query": data.query, "results": results}


@router.post("/match-resume", response_model=ResumeMatchResponse)
def match_resume(data: ResumeMatchRequest, current_student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    if data.student_id is not None and data.student_id != current_student.student_id:
        raise HTTPException(status_code=403, detail="You can only match your own resume.")
    parsed = get_parsed_data(db=db, student_id=current_student.student_id)
    candidate = {
        "name": current_student.name,
        "field_of_study": current_student.field_of_study,
        "skills": parsed.get("skills", []),
        "education": parsed.get("education", []),
        "experience": parsed.get("experience", []),
        "projects": parsed.get("projects", []),
        "certifications": parsed.get("certifications", []),
    }
    query = build_candidate_query(candidate)
    hits = search_jobs(
        query=query,
        top_k=data.top_k,
        candidate_skills=candidate.get("skills", []),
        candidate_domain=current_student.field_of_study,
        hybrid=True,
    )
    matches = []
    for hit in hits:
        job = _knowledge_job(db, hit["job_id"])
        if not job:
            continue
        job_data = job_to_dict(job)
        scored = calculate_match(candidate, job_data)
        matches.append({
            "job_id": job.dataset_job_id,
            "job_title": job.title,
            "company": job.company,
            "location": job.location,
            "work_mode": job.work_mode,
            "job_type": job.job_type,
            "similarity_score": round(hit["similarity_score"], 4),
            "matched_sections": hit["matched_sections"],
            "description": job.description,
            "responsibilities": job_data["responsibilities"],
            "required_skills": job_data["required_skills"],
            "preferred_skills": job_data["preferred_skills"],
            "education_requirements": job.education_requirements,
            "experience_requirements": job.experience,
            "qualifications": job.qualifications,
            "component_scores": scored.get("component_scores"),
            "reasoning": generate_matching_reasoning(candidate, job_data, scored),
            **{
                key: scored[key]
                for key in (
                    "match_score",
                    "matched_skills",
                    "missing_required_skills",
                    "matched_preferred_skills",
                    "missing_preferred_skills",
                    "education_match",
                    "experience_match",
                    "project_match",
                    "recommendation",
                )
            },
        })
    matches.sort(key=lambda item: item["match_score"], reverse=True)
    return {"student_id": current_student.student_id, "total_jobs_retrieved": len(hits), "matches": matches}
