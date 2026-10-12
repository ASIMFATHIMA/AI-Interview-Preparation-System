from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CandidateSkill(Base):
    """
    SQLAlchemy model representing a single skill extracted from a student's resume.
    """
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    skill = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="parsed_skills")


class CandidateEducation(Base):
    """
    SQLAlchemy model representing an education entry extracted from a student's resume.
    """
    __tablename__ = "candidate_education"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    degree = Column(String(200), nullable=True)
    institution = Column(String(255), nullable=True)
    start_year = Column(String(10), nullable=True)
    end_year = Column(String(10), nullable=True)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="parsed_education")


class CandidateExperience(Base):
    """
    SQLAlchemy model representing a work experience entry extracted from a student's resume.
    """
    __tablename__ = "candidate_experience"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    company = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    description = Column(String(2000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="parsed_experience")


class CandidateProject(Base):
    """
    SQLAlchemy model representing a project entry extracted from a student's resume.
    """
    __tablename__ = "candidate_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    project_name = Column(String(255), nullable=True)
    technologies = Column(String(500), nullable=True)
    description = Column(String(2000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="parsed_projects")


class CandidateCertification(Base):
    """
    SQLAlchemy model representing a certification entry extracted from a student's resume.
    """
    __tablename__ = "candidate_certifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    certification_name = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)
    year = Column(String(10), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="parsed_certifications")


class CandidateAchievement(Base):
    """
    SQLAlchemy model representing an achievement entry extracted from a student's resume.
    """
    __tablename__ = "candidate_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    achievement = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="parsed_achievements")
