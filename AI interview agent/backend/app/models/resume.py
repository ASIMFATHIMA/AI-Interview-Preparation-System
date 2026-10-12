from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Resume(Base):
    """
    SQLAlchemy model representing an uploaded student resume and metadata.
    """
    __tablename__ = "resumes"

    resume_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)  # "PDF" or "DOCX"
    file_size = Column(Integer, nullable=False)      # size in bytes
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(20), default="uploaded", nullable=False)  # uploaded, processing, parsed, failed

    # Relationship to Student
    student = relationship("Student", back_populates="resumes")

    def __repr__(self):
        return f"<Resume(resume_id={self.resume_id}, student_id={self.student_id}, original_name='{self.original_name}', status='{self.status}')>"
