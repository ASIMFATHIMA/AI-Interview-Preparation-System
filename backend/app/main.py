import os
import shutil
import uuid

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db, Base
from .config import settings
from .resume_parser import extract_text, UnsupportedFileTypeError
from .llm_extractor import extract_structured_resume

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Internship Application Co-Pilot — API",
    description="Milestone 1: Student profile creation, resume upload, and LLM-based "
    "resume parsing/extraction into a structured Candidate Profile.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# ---------------------------------------------------------------------------
# Student / Profile module (M1.3)
# ---------------------------------------------------------------------------

@app.post("/students", response_model=schemas.StudentOut, tags=["Student Profile"])
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Student).filter(models.Student.email == student.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="A student with this email already exists.")

    db_student = models.Student(name=student.name, email=student.email, phone=student.phone)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@app.get("/students/{student_id}", response_model=schemas.StudentOut, tags=["Student Profile"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


@app.get("/students", response_model=list[schemas.StudentOut], tags=["Student Profile"])
def list_students(db: Session = Depends(get_db)):
    return db.query(models.Student).all()


# ---------------------------------------------------------------------------
# Resume upload (M1.3)
# ---------------------------------------------------------------------------

@app.post(
    "/students/{student_id}/resume",
    response_model=schemas.ResumeOut,
    tags=["Resume Upload"],
)
def upload_resume(
    student_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_resume = models.Resume(
        student_id=student_id,
        filename=file.filename,
        filepath=dest_path,
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume


@app.get(
    "/students/{student_id}/resumes",
    response_model=list[schemas.ResumeOut],
    tags=["Resume Upload"],
)
def list_resumes(student_id: int, db: Session = Depends(get_db)):
    return db.query(models.Resume).filter(models.Resume.student_id == student_id).all()


# ---------------------------------------------------------------------------
# Resume parsing & structured extraction (M1.4)
# ---------------------------------------------------------------------------

@app.post(
    "/students/{student_id}/resume/{resume_id}/parse",
    response_model=schemas.ParseResponse,
    tags=["Resume Parsing"],
)
def parse_resume(student_id: int, resume_id: int, db: Session = Depends(get_db)):
    resume = (
        db.query(models.Resume)
        .filter(models.Resume.id == resume_id, models.Resume.student_id == student_id)
        .first()
    )
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found for this student.")

    # Stage 1: raw text extraction
    try:
        raw_text = extract_text(resume.filepath)
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    resume.raw_text = raw_text
    db.commit()

    # Stage 2: LLM structured extraction
    try:
        extracted = extract_structured_resume(raw_text)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Extraction failed: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Upsert into CandidateProfile + child tables
    profile = (
        db.query(models.CandidateProfile)
        .filter(models.CandidateProfile.student_id == student_id)
        .first()
    )
    if not profile:
        profile = models.CandidateProfile(student_id=student_id)
        db.add(profile)
        db.flush()

    profile.resume_id = resume.id
    profile.summary = extracted.summary
    profile.extracted_raw = extracted.model_dump()

    # Clear old child rows before re-inserting (keeps profile in sync with latest resume)
    db.query(models.Skill).filter(models.Skill.profile_id == profile.id).delete()
    db.query(models.Education).filter(models.Education.profile_id == profile.id).delete()
    db.query(models.Experience).filter(models.Experience.profile_id == profile.id).delete()
    db.query(models.Project).filter(models.Project.profile_id == profile.id).delete()

    for s in extracted.skills:
        db.add(models.Skill(profile_id=profile.id, **s.model_dump()))
    for e in extracted.education:
        db.add(models.Education(profile_id=profile.id, **e.model_dump()))
    for x in extracted.experience:
        db.add(models.Experience(profile_id=profile.id, **x.model_dump()))
    for p in extracted.projects:
        db.add(models.Project(profile_id=profile.id, **p.model_dump()))

    db.commit()
    db.refresh(profile)

    return schemas.ParseResponse(
        resume_id=resume.id,
        profile=_serialize_profile(profile),
        raw_extraction=extracted.model_dump(),
    )


@app.get(
    "/students/{student_id}/profile",
    response_model=schemas.CandidateProfileOut,
    tags=["Candidate Profile"],
)
def get_profile(student_id: int, db: Session = Depends(get_db)):
    profile = (
        db.query(models.CandidateProfile)
        .filter(models.CandidateProfile.student_id == student_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="No profile found for this student yet.")
    return _serialize_profile(profile)


def _serialize_profile(profile: models.CandidateProfile) -> schemas.CandidateProfileOut:
    return schemas.CandidateProfileOut(
        id=profile.id,
        student_id=profile.student_id,
        resume_id=profile.resume_id,
        summary=profile.summary,
        updated_at=profile.updated_at,
        skills=[schemas.SkillItem(name=s.name, category=s.category, proficiency=s.proficiency) for s in profile.skills],
        education=[
            schemas.EducationItem(
                institution=e.institution,
                degree=e.degree,
                field=e.field,
                start_date=e.start_date,
                end_date=e.end_date,
                gpa=e.gpa,
            )
            for e in profile.education
        ],
        experience=[
            schemas.ExperienceItem(
                company=x.company,
                title=x.title,
                start_date=x.start_date,
                end_date=x.end_date,
                description=x.description,
            )
            for x in profile.experience
        ],
        projects=[
            schemas.ProjectItem(
                name=p.name, description=p.description, technologies=p.technologies, link=p.link
            )
            for p in profile.projects
        ],
    )


@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok"}
