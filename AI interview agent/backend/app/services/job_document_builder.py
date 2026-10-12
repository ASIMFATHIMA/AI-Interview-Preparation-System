"""Convert structured jobs into grounded searchable documents."""
import json


def _list(value):
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except json.JSONDecodeError:
            return [item.strip() for item in value.split(",") if item.strip()]
    return value or []


def build_job_document(job):
    title = getattr(job, "title", None) or getattr(job, "job_title", "Internship")
    company = getattr(job, "company", "Company")
    location = getattr(job, "location", "Flexible") or "Flexible"
    description = getattr(job, "description", None) or getattr(job, "job_description", "")
    responsibilities = getattr(job, "responsibilities", [])
    required_skills = getattr(job, "required_skills", [])
    preferred_skills = getattr(job, "preferred_skills", [])
    qualifications = getattr(job, "qualifications", "")
    education = getattr(job, "education_requirements", "")
    experience = getattr(job, "experience", None) or getattr(job, "experience_requirements", "")
    keywords = getattr(job, "keywords", [])
    project = getattr(job, "projects_or_domain", "")

    keyword_list = _list(keywords)
    if project and project not in keyword_list:
        keyword_list.append(project)

    sections = [
        ("Description", description),
        ("Responsibilities", "\n".join(f"- {item}" for item in _list(responsibilities))),
        ("Required Skills", ", ".join(_list(required_skills))),
        ("Preferred Skills", ", ".join(_list(preferred_skills))),
        ("Qualifications", qualifications),
        ("Experience", experience),
        ("Education", education),
        ("Domain/Keywords", ", ".join(keyword_list)),
    ]

    body = [f"Job Title: {title}", f"Company: {company}", f"Location: {location}"]
    for heading, value in sections:
        if value:
            body.extend([f"{heading}:", str(value)])
    return "\n\n".join(body)


def build_record_document(record):
    class Record:
        pass
    job = Record()
    for source, target in (("job_title", "title"), ("job_description", "description"), ("job_id", "dataset_job_id")):
        setattr(job, target, record.get(source))
    for field in ("company", "location", "qualifications", "education_requirements", "experience_requirements", "projects_or_domain"):
        setattr(job, field if field != "experience_requirements" else "experience", record.get(field))
    for field in ("responsibilities", "required_skills", "preferred_skills", "keywords"):
        setattr(job, field, record.get(field, []))
    return build_job_document(job)
