import io
from pathlib import Path


def auth_token(client):
    client.post(
        "/auth/register",
        json={"name": "M3 Candidate", "email": "m3_candidate@example.com", "password": "Password123!"},
    )
    return client.post(
        "/auth/login",
        json={"email": "m3_candidate@example.com", "password": "Password123!"},
    ).json()["access_token"]


def test_m3_complete_workflow(client):
    token = auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload Resume
    sample_path = Path(__file__).parent / "test_resumes" / "sample1_fresh_graduate.docx"
    upload = client.post(
        "/resume/upload",
        headers=headers,
        files={"file": (sample_path.name, io.BytesIO(sample_path.read_bytes()), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert upload.status_code == 201

    # 2. Create target job
    job_payload = {
        "title": "Python AI Intern",
        "company": "ABC Technologies",
        "location": "Remote",
        "experience": "1 year",
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["Docker", "NLP"],
        "education_requirements": "Computer Science",
        "technologies": ["REST API", "PostgreSQL"],
        "description": "Develop backend APIs using FastAPI and Python, and integrate NLP and ML models.",
    }
    job_resp = client.post("/jobs", headers=headers, json=job_payload)
    assert job_resp.status_code == 201
    job_id = job_resp.json()["job_id"]

    # 3. M3.1 Skill Gap Analysis
    skill_gap = client.post(
        "/skill-gap/analyze",
        headers=headers,
        json={"job_id": job_id},
    )
    assert skill_gap.status_code == 200
    sg_data = skill_gap.json()
    assert "Python" in sg_data["matching_skills"] or "Python" in sg_data["matched_skills"]
    assert "FastAPI" in sg_data["matching_skills"] or "FastAPI" in sg_data["matched_skills"]
    assert "REST API" in sg_data["missing_skills"]
    assert "PostgreSQL" in sg_data["partial_skills"]
    assert "recommendations" in sg_data
    assert len(sg_data["recommendations"]) > 0
    assert "experience_gaps" in sg_data
    assert "qualification_gaps" in sg_data

    # 4. M3.2 Resume Customization
    resume_custom = client.post(
        "/resume/customize",
        headers=headers,
        json={"job_id": job_id},
    )
    assert resume_custom.status_code == 200
    rc_data = resume_custom.json()
    assert rc_data["job_title"] == "Python AI Intern"
    assert rc_data["company"] == "ABC Technologies"
    assert "tailored_resume" in rc_data
    assert len(rc_data["tailored_resume"]) > 50
    assert "relevant_skills" in rc_data
    assert "keywords_used" in rc_data

    # Resume history
    rc_hist = client.get("/resume/customize/history", headers=headers)
    assert rc_hist.status_code == 200
    assert len(rc_hist.json()) > 0

    # 5. M3.2 Cover Letter Generation
    cover_letter = client.post(
        "/cover-letter/generate",
        headers=headers,
        json={"job_id": job_id, "company": "ABC Technologies", "job_title": "Python AI Intern", "job_description": job_payload["description"]},
    )
    assert cover_letter.status_code == 200
    cl_data = cover_letter.json()
    assert cl_data["company"] == "ABC Technologies"
    assert "cover_letter" in cl_data
    assert "ABC Technologies" in cl_data["cover_letter"]

    # 6. M3.3 Interview Preparation Guide
    interview_prep = client.post(
        "/interview/prepare",
        headers=headers,
        json={"job_id": job_id},
    )
    assert interview_prep.status_code == 200
    ip_data = interview_prep.json()
    assert len(ip_data["questions"]) > 0
    assert ip_data["questions"][0]["why_this_question_matters"]
    assert ip_data["questions"][0]["preparation_guidance"]

    # 7. M3.3 Mock Interview Interactive Flow
    start_interview = client.post(
        "/interview/start",
        headers=headers,
        json={"job_id": job_id, "interview_type": "technical", "difficulty": "medium", "question_count": 2},
    )
    assert start_interview.status_code == 200
    interview_id = start_interview.json()["interview_id"]

    # Answer Q1
    ans1 = client.post(
        f"/interview/{interview_id}/answer",
        headers=headers,
        json={"answer": "In Python, I utilize virtual environments and write modular functions with type hints and automated unit tests."},
    )
    assert ans1.status_code == 200
    assert ans1.json()["next_question_available"] is True
    assert "score" in ans1.json()
    assert "relevance" in ans1.json()

    # Next Q2
    next_q = client.post(f"/interview/{interview_id}/next", headers=headers)
    assert next_q.status_code == 200

    # Answer Q2
    ans2 = client.post(
        f"/interview/{interview_id}/answer",
        headers=headers,
        json={"answer": "I design RESTful APIs by adhering to standard HTTP verbs, Pydantic schemas, and structured error responses."},
    )
    assert ans2.status_code == 200
    assert ans2.json()["next_question_available"] is False

    # Final Report
    report = client.get(f"/interview/{interview_id}/report", headers=headers)
    assert report.status_code == 200
    rep_data = report.json()
    assert rep_data["status"] == "completed"
    assert rep_data["overall_score"] is not None
    assert "strengths" in rep_data
    assert "recommended_preparation_plan" in rep_data

    # 8. M3.4 Conversational Career Assistant
    chat1 = client.post(
        "/career-assistant/chat",
        headers=headers,
        json={"message": "Which internships match my skills?"},
    )
    assert chat1.status_code == 200
    assert "response" in chat1.json()
    assert "context_used" in chat1.json()
    assert "suggestions" in chat1.json()

    chat2 = client.post(
        "/career-assistant/chat",
        headers=headers,
        json={"message": "What skills am I missing for this job?", "job_id": job_id},
    )
    assert chat2.status_code == 200
    assert chat2.json()["routed_agent"] == "skill_gap"
