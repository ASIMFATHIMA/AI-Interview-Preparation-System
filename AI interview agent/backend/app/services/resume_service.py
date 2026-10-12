import os
import uuid
from typing import List
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.student import Student

# Maximum file size: 5 MB (5 * 1024 * 1024 bytes)
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

# Allowed file extensions and corresponding canonical types
ALLOWED_EXTENSIONS = {
    ".pdf": "PDF",
    ".docx": "DOCX",
}

# Resolve backend uploads/resumes directory path safely
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_and_process_upload(file: UploadFile) -> tuple:
    """
    Validates uploaded file against extension, size limits, and sanitizes filename.
    Returns (clean_original_name, file_type, file_content, file_size).

    IMPORTANT: Reads the file stream and returns the bytes.
    The caller must use these bytes for both saving to disk AND parsing –
    never re-read the UploadFile.file after this call (stream is exhausted).
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload request.",
        )

    # Sanitize and extract extension to prevent path traversal
    clean_original_name = os.path.basename(file.filename)
    _, ext = os.path.splitext(clean_original_name)
    ext_lower = ext.lower()

    if ext_lower not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF and DOCX files are allowed.",
        )

    file_type = ALLOWED_EXTENSIONS[ext_lower]

    # Read content and validate size
    try:
        content = file.file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read uploaded file.",
        )

    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of 5 MB (size: {file_size / (1024 * 1024):.2f} MB).",
        )

    return clean_original_name, file_type, content, file_size


def save_resume_file_and_metadata(
    db: Session,
    student: Student,
    file: UploadFile,
) -> Resume:
    """
    Validates, saves uploaded resume to disk with a UUID-based name,
    and persists metadata in database.

    NOTE: This function reads the file stream. If you also need the bytes
    for parsing, use validate_and_process_upload() directly and handle
    disk writing + DB insert yourself (as done in the /upload route).
    """
    clean_original_name, file_type, content, file_size = validate_and_process_upload(file)

    # Generate unique stored filename (never use original filename)
    _, ext = os.path.splitext(clean_original_name)
    stored_name = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}{ext.lower()}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    # Write file to storage
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store file on disk: {str(e)}",
        )

    # Create Resume DB record
    resume = Resume(
        student_id=student.student_id,
        original_name=clean_original_name,
        stored_name=stored_name,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        status="uploaded",
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def read_resume_file_content(file_path: str) -> bytes:
    """
    Safely reads an already-stored resume file from disk.
    Raises HTTP 404 if the file does not exist.
    Raises HTTP 500 if the file cannot be read.
    """
    # Prevent path traversal: ensure the resolved path is within UPLOAD_DIR
    resolved = os.path.realpath(file_path)
    upload_dir_resolved = os.path.realpath(UPLOAD_DIR)
    if not resolved.startswith(upload_dir_resolved):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: invalid file path.",
        )

    if not os.path.exists(resolved):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found on disk.",
        )

    try:
        with open(resolved, "rb") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read resume file: {str(e)}",
        )


def get_student_resumes(db: Session, student_id: int) -> List[Resume]:
    """
    Retrieves all resume metadata records for a student.
    """
    return db.query(Resume).filter(Resume.student_id == student_id).order_by(Resume.uploaded_at.desc()).all()


def get_student_resume_by_id(db: Session, student_id: int, resume_id: int) -> Resume:
    """
    Retrieves a specific resume ensuring it belongs to the authenticated student.
    """
    resume = db.query(Resume).filter(Resume.resume_id == resume_id, Resume.student_id == student_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or access denied.",
        )
    return resume


def delete_student_resume(db: Session, student_id: int, resume_id: int) -> None:
    """
    Deletes resume metadata and removes the physical file from disk.
    """
    resume = get_student_resume_by_id(db=db, student_id=student_id, resume_id=resume_id)

    # Remove physical file from disk if present
    if os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except OSError:
            pass

    db.delete(resume)
    db.commit()
