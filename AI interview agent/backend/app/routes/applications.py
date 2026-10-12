"""REST routes for the Application Tracking module (M4.1)."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.student import Student
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationInterviewUpdateRequest,
    ApplicationListResponse,
    ApplicationNotesUpdateRequest,
    ApplicationOut,
    ApplicationStatsResponse,
    ApplicationStatusUpdateRequest,
    ApplicationUpdateRequest,
)
from app.services.application_service import (
    _get_owned_application,
    _to_out,
    create_application,
    delete_application,
    get_application_reminders,
    get_application_stats,
    list_applications,
    update_application,
    update_application_interview,
    update_application_notes,
    update_application_status,
)
from app.services.auth_service import get_current_student

router = APIRouter(prefix="/applications", tags=["Application Tracker"])


@router.post(
    "",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new application",
    description="Tracks a new internship/job application for the authenticated student.",
)
def create(
    data: ApplicationCreateRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return create_application(db, current_student, data)


@router.get(
    "",
    response_model=ApplicationListResponse,
    summary="List student applications",
    description="Lists the authenticated student's applications with optional filtering and sorting.",
)
def list_all(
    status: str = Query(None, description="Filter by application status"),
    company: str = Query(None, description="Filter by company name"),
    job_title: str = Query(None, description="Filter by job title"),
    sort_by: str = Query("latest", description="Sort order: latest, oldest, deadline, status, company"),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return list_applications(
        db,
        current_student,
        status_filter=status,
        company=company,
        job_title=job_title,
        sort_by=sort_by,
    )


@router.get(
    "/stats",
    response_model=ApplicationStatsResponse,
    summary="Get application dashboard statistics",
    description="Returns summary counts by status and upcoming deadlines.",
)
def stats(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return get_application_stats(db, current_student)


@router.get(
    "/dashboard",
    response_model=ApplicationStatsResponse,
    summary="Get dashboard statistics",
    description="Returns dashboard statistics for the authenticated student.",
)
def dashboard(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return get_application_stats(db, current_student)


@router.get(
    "/reminders",
    summary="Get deadline and follow-up reminders",
    description="Returns upcoming deadlines, interviews and follow-ups for the authenticated student.",
)
def reminders(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return get_application_reminders(db, current_student)


@router.get(
    "/{application_id}",
    response_model=ApplicationOut,
    summary="Get a single application",
    description="Retrieves one application owned by the authenticated student.",
)
def get_one(
    application_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    application = _get_owned_application(db, current_student, application_id)
    return _to_out(application)


@router.put(
    "/{application_id}",
    response_model=ApplicationOut,
    summary="Update an application",
    description="Updates an existing application owned by the authenticated student.",
)
def update(
    application_id: int,
    data: ApplicationUpdateRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return update_application(db, current_student, application_id, data)


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationOut,
    summary="Update application status",
    description="Updates only the status field of an application owned by the student.",
)
def update_status(
    application_id: int,
    data: ApplicationStatusUpdateRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return update_application_status(db, current_student, application_id, data.status)


@router.patch(
    "/{application_id}/interview",
    response_model=ApplicationOut,
    summary="Update interview details",
    description="Updates the interview details for an application owned by the student.",
)
def update_interview(
    application_id: int,
    data: ApplicationInterviewUpdateRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return update_application_interview(db, current_student, application_id, data)


@router.patch(
    "/{application_id}/notes",
    response_model=ApplicationOut,
    summary="Update notes and follow-up information",
    description="Updates notes, follow-up information and next follow-up date for an application.",
)
def update_notes(
    application_id: int,
    data: ApplicationNotesUpdateRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    return update_application_notes(db, current_student, application_id, data)


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an application",
    description="Deletes an application owned by the authenticated student.",
)
def delete(
    application_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    delete_application(db, current_student, application_id)
    return None