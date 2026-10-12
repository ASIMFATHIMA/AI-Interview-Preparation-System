from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, _ensure_application_columns
from app.models.application import Application
from app.models.job import Job
from app.models.student import Student
from app.schemas.application import ApplicationCreateRequest
from app.services.application_service import create_application


def test_legacy_application_table_is_migrated_and_accepts_new_applications():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine, tables=[Student.__table__, Job.__table__])

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE applications (
                    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    job_id INTEGER,
                    company VARCHAR(200) NOT NULL,
                    location VARCHAR(150),
                    application_date DATETIME,
                    deadline DATETIME,
                    status VARCHAR(50) NOT NULL,
                    notes TEXT,
                    next_action TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO applications
                    (student_id, job_id, company, location, status)
                VALUES (1, NULL, 'Legacy Co', 'Remote', 'Saved')
                """
            )
        )

    _ensure_application_columns(engine)
    _ensure_application_columns(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("applications")}
    assert "company_name" in columns
    assert "job_title" in columns
    assert "application_deadline" in columns
    assert "interview_date" in columns
    assert "follow_up_information" in columns
    with engine.connect() as connection:
        legacy_company = connection.execute(
            text("SELECT company_name FROM applications WHERE application_id = 1")
        ).scalar_one()
    assert legacy_company == "Legacy Co"

    with Session(engine) as db:
        student = Student(
            student_id=1,
            name="Tracker Test",
            email="tracker-test@example.com",
            password_hash="not-used",
        )
        job = Job(
            job_id=180,
            title="AI Intern",
            company="TechNova Solutions",
            description="Internship role supporting AI engineering work.",
        )
        db.add_all([student, job])
        db.commit()

        application = create_application(
            db,
            student,
            ApplicationCreateRequest(
                job_id=180,
                job_title="AI Intern",
                company="TechNova Solutions",
                status="Saved",
            ),
        )

        assert application.application_id is not None
        assert application.job_id == 180
        assert application.status == "Saved"
        assert db.query(Application).filter_by(job_id=180).count() == 1

    engine.dispose()
