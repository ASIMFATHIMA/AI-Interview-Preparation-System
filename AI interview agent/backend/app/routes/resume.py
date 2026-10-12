"""
Resume upload and management routes.
POST   /resume/upload          – Upload, save, parse resume (authenticated)
GET    /resume                 – List all resumes for authenticated student
GET    /resume/{resume_id}     – Get single resume metadata
DELETE /resume/{resume_id}     – Delete resume file + metadata
POST   /resume/{resume_id}/parse – Parse an already-uploaded resume on demand
"""
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import Student
from app.models.resume import Resume
from app.schemas.resume import (
    ResumeUploadResponse,
    ResumeDetailResponse,
    ResumeDeleteResponse,
    ResumeParseResponse,
    ResumeUploadWithParsedResponse,
    ResumeProfileResponse,
)
from app.services.auth_service import get_current_student
from app.services.resume_service import (
    save_resume_file_and_metadata,
    get_student_resumes,
    get_student_resume_by_id,
    delete_student_resume,
    read_resume_file_content,
)
from app.services.resume_parser import parse_resume, save_parsed_data
from app.services.resume_parser import get_parsed_data

router = APIRouter(
    prefix="/resume",
    tags=["Resume Management"],
)


@router.post(
    "/upload",
    response_model=ResumeUploadWithParsedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse student resume",
    description=(
        "Uploads a resume file in PDF or DOCX format (max 5 MB), stores it securely, "
        "registers its metadata in MySQL, and automatically extracts structured data "
        "(name, email, phone, skills, education, experience, projects, certifications, "
        "achievements) from the resume text."
    ),
)
def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX, max 5 MB)"),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Full resume upload + parse flow:
    1. Validate extension (PDF/DOCX) and size (<= 5 MB)
    2. Generate UUID-based stored filename (path traversal safe)
    3. Write file to backend/uploads/resumes/
    4. Persist Resume metadata in MySQL
    5. Extract text from PDF or DOCX bytes
    6. Parse structured information
    7. Update student raw_resume_text + parsed tables
    8. Return structured parsed data along with upload metadata
    """
    # --- Step 1-4: Save file and persist metadata ---
    # validate_and_process_upload reads the file bytes inside save_resume_file_and_metadata
    # and returns the Resume ORM object. We separately get the content here first.
    from app.services.resume_service import validate_and_process_upload
    import uuid
    from datetime import datetime

    clean_name, file_type, content, file_size = validate_and_process_upload(file)

    # Generate unique filename
    _, ext = os.path.splitext(clean_name)
    stored_name = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}{ext.lower()}"

    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    upload_dir = os.path.join(base_dir, "uploads", "resumes")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, stored_name)

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store file on disk: {str(e)}",
        )

    resume = Resume(
        student_id=current_student.student_id,
        original_name=clean_name,
        stored_name=stored_name,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        status="uploaded",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # --- Step 5-8: Parse resume and store structured data ---
    parsed_data = {}
    parse_error = None
    try:
        file_extension = os.path.splitext(clean_name)[1].lower()
        parsed_data = parse_resume(content, file_extension)

        raw_text = parsed_data.get("raw_text", "")
        if raw_text:
            current_student.raw_resume_text = raw_text[:65535]

        if parsed_data.get("name"):
            current_student.name = parsed_data["name"][:100]
        if parsed_data.get("phone"):
            current_student.phone = parsed_data["phone"][:20]
        if parsed_data.get("email"):
            current_student.parsed_resume_email = parsed_data["email"][:150]
        for field in ("location", "linkedin_url", "github_url", "portfolio_url"):
            if parsed_data.get(field):
                setattr(current_student, field, parsed_data[field][:255])
        db.add(current_student)

        save_parsed_data(
            db=db,
            student_id=current_student.student_id,
            parsed_data=parsed_data,
        )

        resume.status = "parsed"
        db.add(resume)
        db.commit()
        db.refresh(resume)

    except ValueError as ve:
        parse_error = str(ve)
    except Exception as exc:
        parse_error = "Resume parsing failed unexpectedly."

    return {
        "success": True,
        "message": "Resume uploaded and processed successfully" if not parse_error else "Resume uploaded successfully",
        "candidate_id": current_student.student_id,
        "resume_id": resume.resume_id,
        "resume": resume,
        "parsed": {
            "name": parsed_data.get("name"),
            "email": parsed_data.get("email"),
            "phone": parsed_data.get("phone"),
            "location": parsed_data.get("location"),
            "linkedin_url": parsed_data.get("linkedin_url"),
            "github_url": parsed_data.get("github_url"),
            "portfolio_url": parsed_data.get("portfolio_url"),
            "skills": parsed_data.get("skills", []),
            "education": parsed_data.get("education", []),
            "experience": parsed_data.get("experience", []),
            "projects": parsed_data.get("projects", []),
            "certifications": parsed_data.get("certifications", []),
            "achievements": parsed_data.get("achievements", []),
        },
        "parse_error": parse_error,
    }


@router.get(
    "/profile/{candidate_id}",
    response_model=ResumeProfileResponse,
    summary="Get the authenticated candidate's parsed resume profile",
)
def get_resume_profile(
    candidate_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    if candidate_id != current_student.student_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume profile not found.")

    resume = get_student_resumes(db=db, student_id=current_student.student_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No resume profile found.")

    latest_resume = resume[0]
    parsed = get_parsed_data(db=db, student_id=current_student.student_id)
    return {
        "candidate_id": current_student.student_id,
        "resume_id": latest_resume.resume_id,
        "resume": latest_resume,
        "profile": {
            "name": current_student.name,
            "email": current_student.parsed_resume_email or current_student.email,
            "phone": current_student.phone,
            "location": current_student.location,
            "linkedin_url": current_student.linkedin_url,
            "github_url": current_student.github_url,
            "portfolio_url": current_student.portfolio_url,
            "skills": parsed.get("skills", []),
            "education": parsed.get("education", []),
            "experience": parsed.get("experience", []),
            "projects": parsed.get("projects", []),
            "certifications": parsed.get("certifications", []),
            "achievements": parsed.get("achievements", []),
        },
    }


@router.get(
    "",
    response_model=List[ResumeDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="List student resumes",
    description="Retrieves metadata of all resumes uploaded by the authenticated student.",
)
def list_resumes(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Returns list of all resumes belonging to the authenticated student.
    """
    return get_student_resumes(db=db, student_id=current_student.student_id)


@router.get(
    "/{resume_id}",
    response_model=ResumeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get resume metadata by ID",
    description="Retrieves metadata of a specific resume belonging to the authenticated student.",
)
def get_resume(
    resume_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Returns metadata for a specific resume if owned by the student.
    """
    return get_student_resume_by_id(
        db=db,
        student_id=current_student.student_id,
        resume_id=resume_id,
    )


@router.delete(
    "/{resume_id}",
    response_model=ResumeDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete resume",
    description="Deletes a resume file and removes its metadata from MySQL.",
)
def delete_resume(
    resume_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Deletes the resume record and removes the physical file from disk.
    """
    delete_student_resume(
        db=db,
        student_id=current_student.student_id,
        resume_id=resume_id,
    )
    return {
        "success": True,
        "message": "Resume deleted successfully",
    }


@router.post(
    "/{resume_id}/parse",
    response_model=ResumeParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Re-parse an existing uploaded resume",
    description="Re-runs the parsing pipeline on an already-uploaded resume file, updating stored structured data.",
)
def reparse_resume(
    resume_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Re-parses an existing uploaded resume:
    - Reads the file from disk (stored securely in uploads/resumes/)
    - Re-extracts all structured data
    - Replaces existing parsed entries in MySQL (no duplicates)
    """
    resume = get_student_resume_by_id(
        db=db,
        student_id=current_student.student_id,
        resume_id=resume_id,
    )

    content = read_resume_file_content(resume.file_path)
    file_extension = os.path.splitext(resume.original_name)[1].lower()

    parsed_data = {}
    parse_error = None
    try:
        parsed_data = parse_resume(content, file_extension)

        raw_text = parsed_data.get("raw_text", "")
        if raw_text:
            current_student.raw_resume_text = raw_text[:65535]
            db.add(current_student)

        if parsed_data.get("name"):
            current_student.name = parsed_data["name"][:100]
        if parsed_data.get("phone"):
            current_student.phone = parsed_data["phone"][:20]
        if parsed_data.get("email"):
            current_student.parsed_resume_email = parsed_data["email"][:150]
        for field in ("location", "linkedin_url", "github_url", "portfolio_url"):
            if parsed_data.get(field):
                setattr(current_student, field, parsed_data[field][:255])
        db.add(current_student)

        save_parsed_data(
            db=db,
            student_id=current_student.student_id,
            parsed_data=parsed_data,
        )

        resume.status = "parsed"
        db.add(resume)
        db.commit()

    except ValueError as ve:
        parse_error = str(ve)
    except Exception as exc:
        parse_error = "Resume parsing failed unexpectedly."

    if parse_error:
        return {
            "success": True,
            "message": parse_error,
            "data": None,
        }

    return {
        "success": True,
        "message": "Resume re-parsed successfully",
        "data": {
            "name": parsed_data.get("name"),
            "email": parsed_data.get("email"),
            "phone": parsed_data.get("phone"),
            "location": parsed_data.get("location"),
            "linkedin_url": parsed_data.get("linkedin_url"),
            "github_url": parsed_data.get("github_url"),
            "portfolio_url": parsed_data.get("portfolio_url"),
            "skills": parsed_data.get("skills", []),
            "education": parsed_data.get("education", []),
            "experience": parsed_data.get("experience", []),
            "projects": parsed_data.get("projects", []),
            "certifications": parsed_data.get("certifications", []),
            "achievements": parsed_data.get("achievements", []),
        },
    }


@router.post("/customize", summary="Generate a tailored resume for target role")
def customize(
    data: dict,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    from app.schemas.agents import ResumeCustomizeRequest
    from app.services.agent_services import customize_resume

    req = ResumeCustomizeRequest(**data)
    return customize_resume(db, current_student, req)


@router.get("/customize/history", summary="Get tailored resume history")
def customize_history(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    from app.models.agents import TailoredResume
    from app.services.agent_services import _load

    records = (
        db.query(TailoredResume)
        .filter(TailoredResume.student_id == current_student.student_id)
        .order_by(TailoredResume.created_at.desc())
        .all()
    )
    return [
        {
            "tailored_resume_id": r.tailored_resume_id,
            "job_id": r.job_id,
            "job_title": r.job_title,
            "company": r.company,
            "tailored_resume": r.tailored_resume,
            "keywords_used": _load(r.keywords_used, []),
            "relevant_skills": _load(r.relevant_skills, []),
            "created_at": r.created_at,
            "success": True,
        }
        for r in records
    ]

