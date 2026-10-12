from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Student(Base):
    """
    SQLAlchemy model representing a registered student profile.
    """
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    location = Column(String(100), nullable=True)
    degree = Column(String(100), nullable=True)
    field_of_study = Column(String(100), nullable=True)
    institution = Column(String(150), nullable=True)
    github_url = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    raw_resume_text = Column(Text, nullable=True)
    parsed_resume_email = Column(String(150), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 1 to N relationship with Resume
    resumes = relationship("Resume", back_populates="student", cascade="all, delete-orphan")

    # 1 to N relationships with parsed resume data
    parsed_skills = relationship("CandidateSkill", back_populates="student", cascade="all, delete-orphan")
    parsed_education = relationship("CandidateEducation", back_populates="student", cascade="all, delete-orphan")
    parsed_experience = relationship("CandidateExperience", back_populates="student", cascade="all, delete-orphan")
    parsed_projects = relationship("CandidateProject", back_populates="student", cascade="all, delete-orphan")
    parsed_certifications = relationship("CandidateCertification", back_populates="student", cascade="all, delete-orphan")
    parsed_achievements = relationship("CandidateAchievement", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student(student_id={self.student_id}, name='{self.name}', email='{self.email}')>"
