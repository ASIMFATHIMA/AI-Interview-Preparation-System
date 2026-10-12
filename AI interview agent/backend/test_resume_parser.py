from io import BytesIO
from pathlib import Path

import pytest
from docx import Document

from app.services.resume_parser import (
    extract_achievements,
    extract_certifications,
    extract_education,
    extract_experience,
    extract_github,
    extract_linkedin,
    extract_location,
    extract_portfolio,
    extract_projects,
    extract_skills,
    parse_resume,
)


def make_docx(*lines):
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    stream = BytesIO()
    document.save(stream)
    return stream.getvalue()


def test_parse_fresh_graduate_docx():
    parsed = parse_resume(make_docx(
        "Asha Raman",
        "asha@example.com | +91 9876543210 | Location: Chennai",
        "SKILLS",
        "Python, React, FastAPI, MySQL",
        "EDUCATION",
        "B.Tech Artificial Intelligence, ABC University 2023 - 2027",
        "PROJECTS",
        "AI Interview Agent",
        "Technologies: Python, FastAPI",
        "CERTIFICATIONS",
        "Python Programming - IBM 2025",
        "ACHIEVEMENTS",
        "Winner, College Hackathon",
    ), ".docx")

    assert parsed["name"] == "Asha Raman"
    assert parsed["email"] == "asha@example.com"
    assert parsed["phone"] == "+919876543210"
    assert parsed["location"] == "Chennai"
    assert {"Python", "React", "FastAPI", "MySQL"}.issubset(parsed["skills"])
    assert parsed["education"]
    assert parsed["projects"]
    assert parsed["certifications"]
    assert parsed["achievements"]


def test_parse_python_experience_and_links():
    text = """Ravi Kumar
ravi@example.com
https://linkedin.com/in/ravi https://github.com/ravi https://ravi.dev
EXPERIENCE
Python Developer Intern | ABC Technologies | June 2025 - July 2025
Developed REST APIs with Django and MySQL.
PROJECTS
Resume Parser
Technologies: Python, Django, FastAPI
"""
    assert extract_experience(text)
    assert extract_projects(text)
    assert "Django" in extract_skills(text)
    assert extract_location(text) is None


def test_missing_optional_sections_return_empty_lists():
    parsed = parse_resume(make_docx(
        "Nina Shah",
        "nina@example.com",
        "SKILLS",
        "Python, Git",
    ), ".docx")

    assert parsed["experience"] == []
    assert parsed["projects"] == []
    assert parsed["certifications"] == []
    assert parsed["achievements"] == []


def test_corrupt_files_are_rejected():
    with pytest.raises(ValueError, match="Failed to extract text"):
        parse_resume(b"not a real document", ".pdf")
    with pytest.raises(ValueError, match="Failed to extract text"):
        parse_resume(b"not a real document", ".docx")


def test_location_and_social_links():
    text = """Alice Johnson
alice@example.com | +1-555-123-4567 | Location: Seattle, WA
LinkedIn: https://linkedin.com/in/alice
GitHub: https://github.com/alice
Portfolio: https://alice.dev
"""
    assert extract_location(text) == "Seattle, WA"
    assert extract_linkedin(text) == "https://linkedin.com/in/alice"
    assert extract_github(text) == "https://github.com/alice"
    assert extract_portfolio(text) == "https://alice.dev"


def test_education_institution_extraction():
    parsed = parse_resume(make_docx(
        "Bob Smith",
        "bob@example.com",
        "EDUCATION",
        "B.Tech Computer Science, MIT, 2020 - 2024",
        "M.S. Artificial Intelligence, Stanford University, 2024 - 2026",
    ), ".docx")

    assert len(parsed["education"]) == 2
    assert parsed["education"][0]["institution"] == "MIT"
    assert parsed["education"][0]["start_year"] == "2020"
    assert parsed["education"][0]["end_year"] == "2024"
    assert parsed["education"][1]["institution"] == "Stanford University"


def test_experience_three_part_format():
    text = """EXPERIENCE
Software Engineer | TechCorp Inc. | June 2023 - Present
Built scalable APIs.
Python Developer Intern | ABC Tech | June 2022 - Aug 2022
Built data pipelines.
"""
    exp = extract_experience(text)
    assert len(exp) == 2
    assert exp[0]["company"] == "TechCorp Inc."
    assert exp[0]["role"] == "Software Engineer"
    assert exp[0]["start_date"] == "June 2023"
    assert exp[0]["end_date"] == "Present"
    assert exp[1]["company"] == "ABC Tech"
    assert exp[1]["role"] == "Python Developer Intern"


@pytest.mark.parametrize(
    "sample_name, expected_counts",
    [
        ("sample1_fresh_graduate", {"education": 1, "projects": 2, "certifications": 2, "achievements": 2}),
        ("sample2_experienced", {"education": 1, "experience": 2, "projects": 2, "certifications": 1, "achievements": 1}),
        ("sample3_data_scientist", {"education": 2, "experience": 2, "projects": 2, "certifications": 2, "achievements": 2}),
        ("sample4_minimal", {"education": 1, "experience": 0, "projects": 0, "certifications": 0, "achievements": 0}),
    ],
)
@pytest.mark.parametrize("extension", [".docx", ".pdf"])
def test_generated_sample_resumes_extract_structured_data(sample_name, expected_counts, extension):
    """The supported sample resume set remains parseable for PDF and DOCX uploads."""
    sample_path = Path(__file__).parent / "test_resumes" / f"{sample_name}{extension}"
    parsed = parse_resume(sample_path.read_bytes(), extension)

    assert parsed["name"]
    assert parsed["email"]
    assert parsed["skills"]
    for field, expected_count in expected_counts.items():
        assert len(parsed[field]) == expected_count
