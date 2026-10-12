"""Service layer for the Application Tracking module (M4.1).

Enforces strict student ownership: every operation is scoped to the
authenticated student's identity and never allows cross-tenant access.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.job import Job
from app.models.student import Student
from app.schemas.application import (
    APPLICATION_STATUSES,
    ApplicationCreateRequest,
    ApplicationInterviewUpdateRequest,
    ApplicationListResponse,
    ApplicationNotesUpdateRequest,
    ApplicationOut,
    ApplicationStatsResponse,
    ApplicationUpdateRequest,
)

logger = logging.getLogger(__name__)

ACTIVE_APPLICATION_STATUSES = {
    "Saved",
    "Planning to Apply",
    "Applied",
    "Application Under Review",
    "Shortlisted",
    "Interview Scheduled",
    "Interview Completed",
    "Interested",
    "Assessment",
    "Interview",
    "Selected",
}

COMPLETED_APPLICATION_STATUSES = {"Offer Received", "Rejected", "Withdrawn"}


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _resolve_status(raw_status: Optional[str]) -> Optional[str]:
    if raw_status is None:
        return None
    cleaned = raw_status.strip()
    if cleaned not in APPLICATION_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select a valid application status.",
        )
    return cleaned


def _to_out(application: Application) -> ApplicationOut:
    """Convert an Application ORM instance into the public response schema."""
    company_name = application.company_name or application.company or ""
    deadline = application.application_deadline or application.deadline
    return ApplicationOut(
        application_id=application.application_id,
        student_id=application.student_id,
        job_id=application.job_id,
        job_title=application.job_title,
        company=company_name,
        company_name=company_name,
        job_description=application.job_description,
        location=application.location,
        application_date=application.application_date,
        application_deadline=deadline,
        deadline=deadline,
        status=application.status,
        interview_date=application.interview_date,
        interview_time=application.interview_time,
        interview_status=application.interview_status,
        interview_type=application.interview_type,
        interview_notes=application.interview_notes,
        interview_outcome=application.interview_outcome,
        notes=application.notes,
        follow_up_information=application.follow_up_information,
        next_follow_up_date=application.next_follow_up_date,
        next_action=application.next_action,
        resume_id=application.resume_id,
        cover_letter_id=application.cover_letter_id,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


def _get_owned_application(
    db: Session,
    student: Student,
    application_id: int,
) -> Application:
    """Fetch an application that belongs to the given student, or raise 404."""
    application = (
        db.query(Application)
        .filter(
            Application.application_id == application_id,
            Application.student_id == student.student_id,
        )
        .first()
    )
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return application


def _ensure_unique_application(db: Session, student_id: int, job_id: Optional[int]) -> None:
    if job_id is None:
        return
    existing = (
        db.query(Application)
        .filter(
            Application.student_id == student_id,
            Application.job_id == job_id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application already exists in your tracker.",
        )


def create_application(
    db: Session,
    student: Student,
    data: ApplicationCreateRequest,
) -> Application:
    """Create a new application record owned by the authenticated student."""
    if data.job_id is not None:
        job = db.query(Job).filter(Job.job_id == data.job_id).first()
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )
        _ensure_unique_application(db, student.student_id, data.job_id)

    status_value = _resolve_status(data.status) or "Saved"
    company_name = _normalize_text(data.company_name or data.company) or "Unspecified Company"
    deadline = data.application_deadline or data.deadline
    application = Application(
        student_id=student.student_id,
        job_id=data.job_id,
        company=company_name,
        company_name=company_name,
        job_title=_normalize_text(data.job_title) or "Untitled Role",
        job_description=_normalize_text(data.job_description) or _normalize_text(data.description),
        location=_normalize_text(data.location),
        application_date=data.application_date,
        application_deadline=deadline,
        deadline=deadline,
        status=status_value,
        interview_date=data.interview_date,
        interview_time=_normalize_text(data.interview_time),
        interview_status=data.interview_status or "Not Scheduled",
        interview_type=_normalize_text(data.interview_type),
        interview_notes=_normalize_text(data.interview_notes),
        interview_outcome=data.interview_outcome or "Pending",
        notes=_normalize_text(data.notes),
        follow_up_information=_normalize_text(data.follow_up_information),
        next_follow_up_date=data.next_follow_up_date,
        next_action=_normalize_text(data.next_action),
        resume_id=data.resume_id,
        cover_letter_id=data.cover_letter_id,
    )
    db.add(application)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        if data.job_id is not None:
            existing = (
                db.query(Application)
                .filter(
                    Application.student_id == student.student_id,
                    Application.job_id == data.job_id,
                )
                .first()
            )
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Application already exists in your tracker.",
                ) from exc
        logger.exception("Unable to save application for student_id=%s", student.student_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save this application. Please try again.",
        ) from exc
    db.refresh(application)
    return application


def update_application(
    db: Session,
    student: Student,
    application_id: int,
    data: ApplicationUpdateRequest,
) -> Application:
    """Update an existing application record. Only the owner may update it."""
    application = _get_owned_application(db, student, application_id)
    update_dict = data.model_dump(exclude_unset=True)

    if "status" in update_dict and update_dict["status"] is not None:
        application.status = _resolve_status(update_dict["status"])

    for field, value in update_dict.items():
        if field in {"status"}:
            continue
        if value is None:
            continue
        if field in {"job_title", "company", "company_name", "location", "notes", "next_action", "job_description", "interview_notes", "follow_up_information", "interview_type", "interview_time"}:
            if isinstance(value, str):
                value = _normalize_text(value)
        if field == "job_id" and value is not None:
            _ensure_unique_application(db, student.student_id, value)
        setattr(application, field, value)

    if "company_name" in update_dict and update_dict["company_name"] is not None:
        company_value = _normalize_text(update_dict["company_name"]) or "Unspecified Company"
        application.company = company_value
        application.company_name = company_value
    elif "company" in update_dict and update_dict["company"] is not None:
        company_value = _normalize_text(update_dict["company"]) or "Unspecified Company"
        application.company = company_value
        application.company_name = company_value

    if "application_deadline" in update_dict:
        deadline_value = update_dict["application_deadline"]
        application.application_deadline = deadline_value
        if deadline_value is not None:
            application.deadline = deadline_value
    elif "deadline" in update_dict and update_dict["deadline"] is not None:
        deadline_value = update_dict["deadline"]
        application.deadline = deadline_value
        application.application_deadline = deadline_value

    application.updated_at = datetime.utcnow()
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def update_application_status(
    db: Session,
    student: Student,
    application_id: int,
    new_status: str,
) -> Application:
    """Update only the status field of an application owned by the student."""
    application = _get_owned_application(db, student, application_id)
    application.status = _resolve_status(new_status)
    application.updated_at = datetime.utcnow()
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def update_application_interview(
    db: Session,
    student: Student,
    application_id: int,
    data: ApplicationInterviewUpdateRequest,
) -> Application:
    """Update interview-related fields for an application."""
    application = _get_owned_application(db, student, application_id)
    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if value is None:
            continue
        if field in {"interview_status", "interview_type", "interview_time", "interview_notes"} and isinstance(value, str):
            value = _normalize_text(value)
        setattr(application, field, value)
    application.updated_at = datetime.utcnow()
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def update_application_notes(
    db: Session,
    student: Student,
    application_id: int,
    data: ApplicationNotesUpdateRequest,
) -> Application:
    """Update notes and follow-up information for an application."""
    application = _get_owned_application(db, student, application_id)
    if data.notes is not None:
        application.notes = _normalize_text(data.notes)
    if data.follow_up_information is not None:
        application.follow_up_information = _normalize_text(data.follow_up_information)
    if data.next_follow_up_date is not None:
        application.next_follow_up_date = data.next_follow_up_date
    if data.next_action is not None:
        application.next_action = _normalize_text(data.next_action)
    application.updated_at = datetime.utcnow()
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def delete_application(
    db: Session,
    student: Student,
    application_id: int,
) -> None:
    """Delete an application record. Only the owner may delete it."""
    application = _get_owned_application(db, student, application_id)
    db.delete(application)
    db.commit()


def list_applications(
    db: Session,
    student: Student,
    status_filter: Optional[str] = None,
    company: Optional[str] = None,
    job_title: Optional[str] = None,
    sort_by: str = "latest",
    role: Optional[str] = None,
) -> ApplicationListResponse:
    """List the student's applications with optional filtering and sorting."""
    query = db.query(Application).filter(Application.student_id == student.student_id)

    resolved_status = _resolve_status(status_filter) if status_filter else None
    if resolved_status:
        query = query.filter(Application.status == resolved_status)
    if company:
        query = query.filter(
            (Application.company.ilike(f"%{company}%")) |
            (Application.company_name.ilike(f"%{company}%"))
        )
    if job_title or role:
        target_title = job_title or role
        query = query.filter(Application.job_title.ilike(f"%{target_title}%"))

    sort_map = {
        "latest": Application.created_at.desc(),
        "oldest": Application.created_at.asc(),
        "deadline": Application.application_deadline.asc(),
        "latest_deadline": Application.application_deadline.desc(),
        "upcoming_deadline": Application.application_deadline.asc(),
        "status": Application.status.asc(),
        "company": Application.company.asc(),
    }
    order_clause = sort_map.get((sort_by or "latest").lower(), Application.created_at.desc())
    applications = query.order_by(order_clause).all()

    return ApplicationListResponse(
        total=len(applications),
        applications=[_to_out(app) for app in applications],
    )


def get_application_stats(
    db: Session,
    student: Student,
    upcoming_limit: int = 5,
) -> ApplicationStatsResponse:
    """Compute dashboard statistics and upcoming deadlines for the student."""
    applications = (
        db.query(Application)
        .filter(Application.student_id == student.student_id)
        .all()
    )

    stats = ApplicationStatsResponse(
        total=len(applications),
        saved=0,
        interested=0,
        applied=0,
        assessment=0,
        interview=0,
        selected=0,
        rejected=0,
        withdrawn=0,
        active=0,
        interviews_scheduled=0,
        offers_received=0,
        pending_applications=0,
    )

    now = datetime.utcnow()
    upcoming_deadlines = []

    for app in applications:
        key = app.status.lower().replace(" ", "_")
        if hasattr(stats, key):
            setattr(stats, key, getattr(stats, key) + 1)
        if app.status in ACTIVE_APPLICATION_STATUSES:
            stats.active += 1
        if app.status == "Offer Received":
            stats.offers_received += 1
        if app.status == "Rejected":
            stats.rejected += 1
        if app.status == "Interview Scheduled":
            stats.interviews_scheduled += 1
        if app.interview_date and app.interview_date >= now:
            stats.interviews_scheduled += 1
        if app.deadline and app.deadline >= now:
            upcoming_deadlines.append(_to_out(app))
        if app.status in {"Saved", "Planning to Apply", "Applied", "Application Under Review", "Shortlisted", "Interview Scheduled", "Interview Completed"}:
            stats.pending_applications += 1

    upcoming_deadlines.sort(key=lambda app: app.application_deadline or now)
    stats.upcoming_deadlines = upcoming_deadlines[:upcoming_limit]
    stats.upcoming_deadlines_count = len(upcoming_deadlines)
    return stats


def get_application_reminders(
    db: Session,
    student: Student,
) -> dict:
    """Return upcoming deadlines, interviews and follow-up reminders."""
    applications = (
        db.query(Application)
        .filter(Application.student_id == student.student_id)
        .all()
    )
    now = datetime.utcnow()

    upcoming_deadlines = [
        _to_out(app)
        for app in applications
        if app.application_deadline or app.deadline
    ]
    upcoming_deadlines = sorted(
        upcoming_deadlines,
        key=lambda app: app.application_deadline or app.deadline or now,
    )

    scheduled_interviews = [
        _to_out(app)
        for app in applications
        if app.interview_date and app.interview_date >= now
    ]
    scheduled_interviews = sorted(
        scheduled_interviews,
        key=lambda app: app.interview_date or now,
    )

    follow_ups = [
        _to_out(app)
        for app in applications
        if app.next_follow_up_date and app.next_follow_up_date >= now
    ]
    follow_ups = sorted(
        follow_ups,
        key=lambda app: app.next_follow_up_date or now,
    )

    pending = [
        _to_out(app)
        for app in applications
        if app.status in {"Saved", "Planning to Apply", "Applied", "Application Under Review", "Shortlisted", "Interview Scheduled", "Interview Completed"}
    ]

    return {
        "upcoming_deadlines": upcoming_deadlines,
        "scheduled_interviews": scheduled_interviews,
        "upcoming_follow_ups": follow_ups,
        "pending_applications": pending,
    }