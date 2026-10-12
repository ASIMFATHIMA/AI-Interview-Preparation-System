"""Persistence model for student internship/job applications (M4.1)."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Application(Base):
    """
    Tracks a student's internship/job application lifecycle.
    Status is only changed by explicit user actions.
    """

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("student_id", "job_id", name="uq_applications_student_job"),
    )

    application_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(
        Integer,
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id = Column(
        Integer,
        ForeignKey("jobs.job_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    company = Column(String(200), nullable=False, default="")
    company_name = Column(String(200), nullable=True)
    job_title = Column(String(200), nullable=False)
    job_description = Column(Text, nullable=True)
    location = Column(String(150), nullable=True)
    application_date = Column(DateTime(timezone=True), nullable=True)
    application_deadline = Column(DateTime(timezone=True), nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="Saved")
    interview_date = Column(DateTime(timezone=True), nullable=True)
    interview_time = Column(String(50), nullable=True)
    interview_status = Column(String(50), nullable=True, default="Not Scheduled")
    interview_type = Column(String(50), nullable=True)
    interview_notes = Column(Text, nullable=True)
    interview_outcome = Column(String(50), nullable=True, default="Pending")
    notes = Column(Text, nullable=True)
    follow_up_information = Column(Text, nullable=True)
    next_follow_up_date = Column(DateTime(timezone=True), nullable=True)
    next_action = Column(Text, nullable=True)
    resume_id = Column(Integer, nullable=True)
    cover_letter_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    student = relationship("Student")
    job = relationship("Job")

    def __repr__(self):
        return (
            f"<Application(application_id={self.application_id}, "
            f"student_id={self.student_id}, job_title='{self.job_title}', "
            f"status='{self.status}')>"
        )