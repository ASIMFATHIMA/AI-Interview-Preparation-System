from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="student", cascade="all, delete-orphan")
    profile = relationship(
        "CandidateProfile",
        back_populates="student",
        uselist=False,
        cascade="all, delete-orphan",
    )
    applications = relationship(
        "Application", back_populates="student", cascade="all, delete-orphan"
    )


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    filepath = Column(String(1000), nullable=False)
    raw_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="resumes")


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True, nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    summary = Column(Text, nullable=True)
    extracted_raw = Column(JSON, nullable=True)  # full raw LLM extraction, for audit/debug
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="profile")
    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")
    education = relationship("Education", back_populates="profile", cascade="all, delete-orphan")
    experience = relationship(
        "Experience", back_populates="profile", cascade="all, delete-orphan"
    )
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # e.g. "language", "framework", "soft-skill"
    proficiency = Column(String(50), nullable=True)  # e.g. "beginner/intermediate/advanced"

    profile = relationship("CandidateProfile", back_populates="skills")


class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    institution = Column(String(500), nullable=True)
    degree = Column(String(255), nullable=True)
    field = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    gpa = Column(String(50), nullable=True)

    profile = relationship("CandidateProfile", back_populates="education")


class Experience(Base):
    __tablename__ = "experience"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    company = Column(String(500), nullable=True)
    title = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    profile = relationship("CandidateProfile", back_populates="experience")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    name = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    technologies = Column(String(500), nullable=True)
    link = Column(String(500), nullable=True)

    profile = relationship("CandidateProfile", back_populates="projects")


class Application(Base):
    """Placeholder model for the Application Tracking Module (built out in a later milestone)."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    job_title = Column(String(500), nullable=True)
    company = Column(String(500), nullable=True)
    status = Column(String(50), default="applied")
    applied_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="applications")
