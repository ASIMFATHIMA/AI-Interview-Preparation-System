"""Validation and normalization for curated job records."""
import re

JOB_FIELDS = (
    "job_id", "job_title", "company", "location", "work_mode", "job_type",
    "job_description", "responsibilities", "required_skills", "preferred_skills",
    "qualifications", "experience_requirements", "education_requirements",
    "projects_or_domain", "keywords", "source", "status",
)

SKILL_ALIASES = {
    "fast api": "FastAPI",
    "fastapi": "FastAPI",
    "scikit learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "machine-learning": "Machine Learning",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "gen ai": "Generative AI",
    "generative ai": "Generative AI",
    "restful api": "REST API",
    "rest api": "REST API",
    "rest": "REST API",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "llm": "LLM",
    "large language models": "LLM",
    "large language model": "LLM",
    "rag": "RAG",
    "spring": "Spring Boot",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "sql": "SQL",
    "nosql": "NoSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "cyber security": "Cybersecurity",
    "cybersecurity": "Cybersecurity",
    "infosec": "Cybersecurity",
    "information security": "Cybersecurity",
    "py": "Python",
    "python3": "Python",
    "db": "Database",
    "database": "Database",
    "mysql": "MySQL",
}

RELEVANT_TERMS = {
    "artificial intelligence", "machine learning", "data science", "data analytics",
    "python", "backend", "full stack", "frontend", "front-end", "software engineering",
    "generative ai", "nlp", "cloud", "devops", "deep learning", "api", "developer",
    "java", "spring", "cybersecurity", "security", "database", "sql", "html", "css",
    "react", "network security", "vulnerability", "web development", "docker",
}


def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_skill(value):
    cleaned = clean_text(value)
    if not cleaned:
        return ""
    return SKILL_ALIASES.get(cleaned.lower(), cleaned)


def normalize_skills(values):
    if isinstance(values, str):
        values = [item for item in values.split(",") if item.strip()]
    result = []
    seen = set()
    for value in values or []:
        skill = normalize_skill(value)
        key = skill.casefold()
        if skill and key not in seen:
            seen.add(key)
            result.append(skill)
    return result


def clean_record(record):
    cleaned = {field: record.get(field) for field in JOB_FIELDS}
    for field in (
        "job_id", "job_title", "company", "location", "work_mode", "job_type",
        "job_description", "qualifications", "experience_requirements",
        "education_requirements", "projects_or_domain", "source", "status"
    ):
        cleaned[field] = clean_text(cleaned.get(field))
    cleaned["responsibilities"] = [
        clean_text(item) for item in (cleaned["responsibilities"] or []) if clean_text(item)
    ]
    cleaned["required_skills"] = normalize_skills(cleaned["required_skills"])
    cleaned["preferred_skills"] = normalize_skills(cleaned["preferred_skills"])
    cleaned["keywords"] = normalize_skills(cleaned["keywords"])
    return cleaned


def validate_record(record):
    missing = [
        field for field in ("job_id", "job_title", "company", "job_description")
        if not clean_text(record.get(field))
    ]
    if not record.get("required_skills"):
        missing.append("required_skills")
    text = " ".join(clean_text(record.get(field)) for field in ("job_title", "job_description", "projects_or_domain", "keywords"))
    irrelevant = not any(term in text.casefold() for term in RELEVANT_TERMS)
    return missing, irrelevant


def clean_records(records):
    seen_ids = set()
    seen_content = set()
    cleaned_records = []
    duplicates_removed = 0
    incomplete_records = 0
    irrelevant_records = 0

    for record in records:
        cleaned = clean_record(record)
        missing, irrelevant = validate_record(cleaned)
        if missing:
            incomplete_records += 1
            continue
        if irrelevant:
            irrelevant_records += 1
            continue

        job_id_key = cleaned["job_id"].casefold()
        content_key = (cleaned["company"].casefold(), cleaned["job_title"].casefold(), cleaned["location"].casefold())

        if job_id_key in seen_ids or content_key in seen_content:
            duplicates_removed += 1
            continue

        seen_ids.add(job_id_key)
        seen_content.add(content_key)
        cleaned_records.append(cleaned)

    return cleaned_records, {
        "total_records": len(records),
        "duplicates_removed": duplicates_removed,
        "incomplete_records": incomplete_records,
        "irrelevant_records": irrelevant_records,
        "final_records": len(cleaned_records),
    }