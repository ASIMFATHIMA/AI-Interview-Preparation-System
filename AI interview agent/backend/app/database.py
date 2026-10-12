import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file
load_dotenv()

# Read the database URL from .env or construct from discrete variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "ai_career_companion")
    DATABASE_URL = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create SQLAlchemy engine
# pool_pre_ping checks connectivity before giving out connections from the pool
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Session factory bound to engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all database models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a SQLAlchemy database session per request
    and guarantees proper closing upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Checks if the MySQL database is reachable.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def init_db():
    """
    Creates all database tables defined in models if they do not exist.
    """
    import app.models  # Ensures all models are registered with Base.metadata
    Base.metadata.create_all(bind=engine)
    _ensure_job_columns()
    _ensure_application_columns()


def _ensure_job_columns():
    """Add M2 job columns to databases created by the earlier milestone."""
    try:
        inspector = inspect(engine)
        if not inspector.has_table("jobs"):
            return
        existing = {column["name"] for column in inspector.get_columns("jobs")}
        columns = {
            "dataset_job_id": "VARCHAR(32)", "work_mode": "VARCHAR(30)", "job_type": "VARCHAR(30)",
            "qualifications": "TEXT", "projects_or_domain": "VARCHAR(200)", "keywords": "TEXT",
            "source": "VARCHAR(100)", "status": "VARCHAR(30)",
        }
        with engine.begin() as connection:
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE jobs ADD COLUMN {name} {definition}"))
    except Exception as exc:
        print(f"[Warning] Job schema migration could not be applied: {exc}")


def _ensure_application_columns(bind=engine):
    """Add application-tracker fields to databases with the earlier table schema."""
    inspector = inspect(bind)
    if not inspector.has_table("applications"):
        return
    has_jobs_table = inspector.has_table("jobs")

    existing = {column["name"] for column in inspector.get_columns("applications")}
    columns = {
        "company_name": "VARCHAR(200) NULL",
        "job_title": "VARCHAR(200) NOT NULL DEFAULT ''",
        "job_description": "TEXT NULL",
        "application_deadline": "DATETIME NULL",
        "interview_date": "DATETIME NULL",
        "interview_time": "VARCHAR(50) NULL",
        "interview_status": "VARCHAR(50) NULL",
        "interview_type": "VARCHAR(50) NULL",
        "interview_notes": "TEXT NULL",
        "interview_outcome": "VARCHAR(50) NULL",
        "follow_up_information": "TEXT NULL",
        "next_follow_up_date": "DATETIME NULL",
        "resume_id": "INTEGER NULL",
        "cover_letter_id": "INTEGER NULL",
    }
    added_columns = set()
    with bind.begin() as connection:
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(
                    text(f"ALTER TABLE applications ADD COLUMN {name} {definition}")
                )
                added_columns.add(name)

        if "company_name" in added_columns:
            connection.execute(
                text(
                    "UPDATE applications SET company_name = company "
                    "WHERE company_name IS NULL"
                )
            )
        if "application_deadline" in added_columns:
            connection.execute(
                text(
                    "UPDATE applications SET application_deadline = deadline "
                    "WHERE application_deadline IS NULL"
                )
            )
        if "job_title" in added_columns and has_jobs_table:
            connection.execute(
                text(
                    "UPDATE applications SET job_title = ("
                    "SELECT title FROM jobs WHERE jobs.job_id = applications.job_id"
                    ") WHERE job_title = '' AND job_id IS NOT NULL "
                    "AND EXISTS (SELECT 1 FROM jobs "
                    "WHERE jobs.job_id = applications.job_id)"
                )
            )