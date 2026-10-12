"""
Business logic and auxiliary services package.
"""
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    register_student,
    authenticate_student,
    get_current_student,
)
from app.services.profile_service import update_student_profile
from app.services.resume_service import (
    save_resume_file_and_metadata,
    get_student_resumes,
    get_student_resume_by_id,
    delete_student_resume,
)
from app.services.resume_parser import (
    parse_resume,
    save_parsed_data,
    get_parsed_data,
    extract_pdf_text,
    extract_docx_text,
    clean_text,
    extract_email,
    extract_phone,
    extract_name,
    extract_skills,
    extract_education,
    extract_experience,
    extract_projects,
    extract_certifications,
    extract_achievements,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "register_student",
    "authenticate_student",
    "get_current_student",
    "update_student_profile",
    "save_resume_file_and_metadata",
    "get_student_resumes",
    "get_student_resume_by_id",
    "delete_student_resume",
    "parse_resume",
    "save_parsed_data",
    "get_parsed_data",
    "extract_pdf_text",
    "extract_docx_text",
    "clean_text",
    "extract_email",
    "extract_phone",
    "extract_name",
    "extract_skills",
    "extract_education",
    "extract_experience",
    "extract_projects",
    "extract_certifications",
    "extract_achievements",
]
