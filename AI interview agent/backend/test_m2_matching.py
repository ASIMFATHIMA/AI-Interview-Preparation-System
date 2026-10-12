import json

from app.services.candidate_query_builder import build_candidate_query
from app.services.job_chunker import chunk_job_document
from app.services.job_data_cleaner import clean_records
from app.services.job_matcher import calculate_match
from app.services.vector_store import search_jobs


def test_cleaner_removes_duplicates_and_normalizes_skills():
    records = [
        {
            "job_id": "1",
            "job_title": "Python Developer Intern",
            "company": "TechCorp",
            "location": "Bengaluru",
            "job_description": "Python backend role",
            "required_skills": [" fast api", "FastAPI", "Python", "sklearn"],
        },
        {
            "job_id": "2",
            "job_title": "Python Developer Intern",
            "company": "TechCorp",
            "location": "Bengaluru",
            "job_description": "Python backend role",
            "required_skills": ["Python"],
        },
    ]
    cleaned, report = clean_records(records)
    assert len(cleaned) == 1
    assert "FastAPI" in cleaned[0]["required_skills"]
    assert "Scikit-learn" in cleaned[0]["required_skills"]
    assert report["duplicates_removed"] == 1


def test_cleaner_filters_incomplete_and_irrelevant():
    records = [
        {
            "job_id": "JOB1",
            "job_title": "",  # missing title
            "company": "Corp",
            "job_description": "Desc",
            "required_skills": ["Python"],
        },
        {
            "job_id": "JOB2",
            "job_title": "Real Estate Broker",  # irrelevant
            "company": "Homes",
            "job_description": "Sell apartments and show properties",
            "required_skills": ["Sales"],
        },
        {
            "job_id": "JOB3",
            "job_title": "AI Intern",
            "company": "AI Labs",
            "job_description": "Build deep learning models with Python",
            "required_skills": ["Python", "Machine Learning"],
        },
    ]
    cleaned, report = clean_records(records)
    assert len(cleaned) == 1
    assert cleaned[0]["job_id"] == "JOB3"
    assert report["incomplete_records"] == 1
    assert report["irrelevant_records"] == 1


def test_section_chunking_preserves_metadata_and_chunk_id():
    metadata = {
        "job_id": "JOB001",
        "job_title": "Machine Learning Intern",
        "company": "Vertex Digital",
    }
    document = (
        "Job Title: Machine Learning Intern\n\n"
        "Required Skills:\nPython, Machine Learning, Pandas\n\n"
        "Education:\nB.Tech Computer Science or related field\n\n"
        "Responsibilities:\n- Build predictive models\n- Clean data"
    )
    chunks = chunk_job_document(document, metadata)
    assert len(chunks) >= 3
    assert {chunk["section"] for chunk in chunks} == {"Required Skills", "Education", "Responsibilities"}
    for chunk in chunks:
        assert chunk["job_id"] == "JOB001"
        assert chunk["job_title"] == "Machine Learning Intern"
        assert chunk["company"] == "Vertex Digital"
        assert "chunk_id" in chunk
        assert chunk["chunk_id"].startswith("JOB001_")


def test_candidate_query_contains_stored_evidence():
    query = build_candidate_query({
        "skills": ["Python", "NLP", "RAG"],
        "education": [{"degree": "B.Tech Artificial Intelligence"}],
        "projects": [{"project_name": "RAG Chatbot"}],
        "experience": [],
    })
    assert "Python" in query
    assert "RAG Chatbot" in query
    assert "B.Tech Artificial Intelligence" in query


def test_matcher_reports_strong_and_missing_skills():
    candidate = {
        "skills": ["Python", "FastAPI", "postgres", "sklearn"],
        "education": [{"degree": "B.Tech Computer Science"}],
        "projects": [{"project_name": "FastAPI REST Service with PostgreSQL"}],
        "experience": [],
    }
    job = {
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "SQL"],
        "preferred_skills": ["Docker"],
        "education_requirements": "B.Tech in Computer Science or IT",
        "experience_requirements": "0-1 years; academic projects accepted",
        "keywords": ["backend", "api"],
        "responsibilities": ["Build asynchronous Python APIs using FastAPI and PostgreSQL"],
    }
    result = calculate_match(candidate, job)
    assert "Python" in result["matched_skills"]
    assert "FastAPI" in result["matched_skills"]
    assert "SQL" in result["missing_required_skills"]
    assert result["match_score"] >= 60.0
    assert result["recommendation"] in {"Partial Match", "Good Match", "Strong Match"}
    assert "component_scores" in result
    assert "required_skills" in result["component_scores"]
    assert "education" in result["component_scores"]


def test_vector_search_deduplicates_jobs():
    results = search_jobs("machine learning python intern", top_k=5)
    assert len(results) <= 5
    job_ids = [r["job_id"] for r in results]
    assert len(job_ids) == len(set(job_ids)), "Search results must contain unique jobs without duplicate job IDs"


if __name__ == "__main__":
    tests = [
        test_cleaner_removes_duplicates_and_normalizes_skills,
        test_cleaner_filters_incomplete_and_irrelevant,
        test_section_chunking_preserves_metadata_and_chunk_id,
        test_candidate_query_contains_stored_evidence,
        test_matcher_reports_strong_and_missing_skills,
        test_vector_search_deduplicates_jobs,
    ]
    print(f"Running {len(tests)} M2 unit tests...")
    for test in tests:
        test()
        print(f"  [PASS] {test.__name__}")
    print("\nAll M2 unit tests passed successfully!")

