"""Shared job persistence model used by legacy agents and M2 retrieval."""
import json

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_job_id = Column(String(32), unique=True, nullable=True, index=True)
    title = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    location = Column(String(150), nullable=True)
    work_mode = Column(String(30), nullable=True, default="Hybrid")
    job_type = Column(String(30), nullable=True, default="Internship")
    experience = Column(String(100), nullable=True)
    required_skills = Column(Text, nullable=False, default="[]")
    preferred_skills = Column(Text, nullable=False, default="[]")
    education_requirements = Column(Text, nullable=True)
    responsibilities = Column(Text, nullable=True)
    technologies = Column(Text, nullable=False, default="[]")
    description = Column(Text, nullable=False)
    qualifications = Column(Text, nullable=True)
    projects_or_domain = Column(String(200), nullable=True)
    keywords = Column(Text, nullable=False, default="[]")
    source = Column(String(100), nullable=False, default="Curated Sample Dataset")
    status = Column(String(30), nullable=False, default="Active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @staticmethod
    def decode(value, default=None):
        if not value:
            return [] if default is None else default
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return [] if default is None else default
