"""Import cleaned dataset records into the existing jobs table."""
import json
import sys
from pathlib import Path

from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.database import SessionLocal, init_db
from app.models.job import Job
from app.services.job_data_cleaner import clean_records

DATA_PATH = ROOT / "data" / "jobs_dataset.json"


def as_json(value):
    return json.dumps(value or [], ensure_ascii=True)


def import_jobs(db: Session, records):
    clean, report = clean_records(records)
    inserted = 0
    updated = 0
    for record in clean:
        job = db.query(Job).filter(Job.dataset_job_id == record["job_id"]).first()
        if job:
            job.title = record["job_title"]
            job.company = record["company"]
            job.location = record["location"]
            job.work_mode = record["work_mode"]
            job.job_type = record["job_type"]
            job.experience = record["experience_requirements"]
            job.required_skills = as_json(record["required_skills"])
            job.preferred_skills = as_json(record["preferred_skills"])
            job.education_requirements = record["education_requirements"]
            job.responsibilities = as_json(record["responsibilities"])
            job.technologies = as_json(record["required_skills"] + record["preferred_skills"])
            job.description = record["job_description"]
            job.qualifications = record["qualifications"]
            job.projects_or_domain = record["projects_or_domain"]
            job.keywords = as_json(record["keywords"])
            job.source = record["source"]
            job.status = record["status"]
            updated += 1
        else:
            job = Job(
                dataset_job_id=record["job_id"],
                title=record["job_title"],
                company=record["company"],
                location=record["location"],
                work_mode=record["work_mode"],
                job_type=record["job_type"],
                experience=record["experience_requirements"],
                required_skills=as_json(record["required_skills"]),
                preferred_skills=as_json(record["preferred_skills"]),
                education_requirements=record["education_requirements"],
                responsibilities=as_json(record["responsibilities"]),
                technologies=as_json(record["required_skills"] + record["preferred_skills"]),
                description=record["job_description"],
                qualifications=record["qualifications"],
                projects_or_domain=record["projects_or_domain"],
                keywords=as_json(record["keywords"]),
                source=record["source"],
                status=record["status"],
            )
            db.add(job)
            inserted += 1
    db.commit()
    return report, inserted, updated


def main():
    init_db()
    records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        report, inserted, updated = import_jobs(db, records)
        print("Loading dataset...")
        print(f"Total records: {report['total_records']}")
        print(f"Clean records: {report['final_records']}")
        print(f"Inserted: {inserted}")
        print(f"Updated: {updated}")
        print("Import completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
