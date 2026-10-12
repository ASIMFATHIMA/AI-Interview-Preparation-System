"""End-to-end tests for the six career-agent APIs."""
import io
from pathlib import Path


def auth_token(client):
    client.post(
        "/auth/register",
        json={"name": "Agent Candidate", "email": "agent@example.com", "password": "Password123!"},
    )
    return client.post(
        "/auth/login",
        json={"email": "agent@example.com", "password": "Password123!"},
    ).json()["access_token"]


def job_payload():
    return {
        "title": "Backend Engineer",
        "company": "Example Labs",
        "location": "Remote",
        "experience": "2 years",
        "required_skills": ["Python", "AWS"],
        "preferred_skills": ["Docker"],
        "education_requirements": "Computer Science",
        "technologies": ["FastAPI", "PostgreSQL"],
        "description": "Build reliable APIs and deploy services for our developer platform.",
    }


def test_agent_workflows_are_authenticated_and_persisted(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    sample_path = Path(__file__).parent / "test_resumes" / "sample1_fresh_graduate.docx"
    upload = client.post(
        "/resume/upload",
        headers=headers,
        files={"file": (sample_path.name, io.BytesIO(sample_path.read_bytes()), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert upload.status_code == 201

    job_response = client.post("/jobs", headers=headers, json=job_payload())
    assert job_response.status_code == 201
    job_id = job_response.json()["job_id"]

    match = client.post(
        "/api/matching/analyze",
        headers=headers,
        json={"job_id": job_id},
    )
    assert match.status_code == 200
    assert "Python" in match.json()["matched_skills"]
    assert "AWS" in match.json()["missing_skills"]
    assert 0 <= match.json()["match_score"] <= 100
    match_history = client.get("/api/matching/history", headers=headers)
    assert match_history.status_code == 200
    assert match_history.json()[0]["match_id"] == match.json()["match_id"]

    gaps = client.post(
        "/api/skill-gap/analyze",
        headers=headers,
        json={"job_id": job_id},
    )
    assert gaps.status_code == 200
    assert gaps.json()["skill_gaps"][0]["skill"] == "AWS"
    assert "PostgreSQL" in gaps.json()["partial_skills"]
    assert gaps.json()["skill_match_score"] < 100
    assert gaps.json()["skill_gap_score"] == 100 - gaps.json()["skill_match_score"]
    assert gaps.json()["learning_roadmap"]
    assert client.get("/api/skill-gap/history", headers=headers).status_code == 200

    letter = client.post(
        "/api/cover-letter/generate",
        headers=headers,
        json={
            "job_id": job_id,
            "company": "Example Labs",
            "job_title": "Backend Engineer",
            "job_description": job_payload()["description"],
        },
    )
    assert letter.status_code == 200
    assert "Example Labs" in letter.json()["cover_letter"]
    assert client.get("/api/cover-letter", headers=headers).json()[0]["company"] == "Example Labs"

    interview = client.post(
        "/api/interview/start",
        headers=headers,
        json={"job_id": job_id, "interview_type": "technical", "question_count": 1},
    )
    assert interview.status_code == 200
    interview_id = interview.json()["interview_id"]
    detail = client.get(f"/api/interview/{interview_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["question_count"] == 1

    answer = client.post(
        f"/api/interview/{interview_id}/answer",
        headers=headers,
        json={"answer": "I would define the requirements, implement tests, and measure the result."},
    )
    assert answer.status_code == 200
    assert answer.json()["next_question_available"] is False

    result = client.get(f"/api/interview/{interview_id}/result", headers=headers)
    assert result.status_code == 200
    assert result.json()["status"] == "completed"
    assert client.get("/api/interview", headers=headers).json()[0]["interview_id"] == interview_id

    chat = client.post(
        "/api/career/chat",
        headers=headers,
        json={"message": "What skills should I learn next?"},
    )
    assert chat.status_code == 200
    assert chat.json()["routed_agent"] == "skill_gap"
    assert client.get("/api/career/history", headers=headers).json()[0]["chat_id"] == chat.json()["chat_id"]


def test_skill_gap_rejects_job_without_detectable_skills(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    job_response = client.post(
        "/jobs",
        headers=headers,
        json={
            "title": "People Coordinator",
            "company": "Example Labs",
            "description": "Coordinate communication and stakeholder meetings.",
        },
    )
    response = client.post(
        "/api/skill-gap/analyze",
        headers=headers,
        json={"job_id": job_response.json()["job_id"]},
    )
    assert response.status_code == 400
    assert "Unable to identify job skills" in response.json()["detail"]


def test_skill_gap_accepts_inline_job_description(client):
    token = auth_token(client)
    response = client.post(
        "/api/skill-gap/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "job_title": "Python Backend Developer",
            "company": "Example Labs",
            "job_description": "Build Python APIs with FastAPI and Docker for production services.",
        },
    )
    assert response.status_code == 200
    assert response.json()["job_title"] == "Python Backend Developer"
    assert response.json()["company"] == "Example Labs"
    assert "Python" in response.json()["matched_skills"] or "Python" in response.json()["missing_skills"]


def test_agent_endpoints_require_authentication(client):
    assert client.get("/jobs").status_code == 401
    assert client.post("/api/matching/analyze", json={}).status_code == 401
    assert client.post("/api/career/chat", json={"message": "hello"}).status_code == 401
