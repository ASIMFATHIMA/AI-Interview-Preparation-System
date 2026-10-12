def test_authenticated_student_can_track_job_and_duplicate_is_conflict(client):
    registration = client.post(
        "/auth/register",
        json={
            "name": "Tracker Test",
            "email": "tracker-test@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "tracker-test@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    job_response = client.post(
        "/jobs",
        headers=headers,
        json={
            "title": "AI Intern",
            "company": "TechNova Solutions",
            "description": "Internship role supporting AI engineering work.",
        },
    )
    assert job_response.status_code == 201
    job_id = job_response.json()["job_id"]

    payload = {
        "job_id": job_id,
        "job_title": "AI Intern",
        "company": "TechNova Solutions",
        "status": "Saved",
    }
    created = client.post("/applications", headers=headers, json=payload)
    assert created.status_code == 201
    assert created.json()["job_id"] == job_id
    assert created.json()["status"] == "Saved"

    duplicate = client.post("/applications", headers=headers, json=payload)
    assert duplicate.status_code == 409

    tracker = client.get("/applications", headers=headers)
    assert tracker.status_code == 200
    assert tracker.json()["total"] == 1
    assert tracker.json()["applications"][0]["job_title"] == "AI Intern"


def test_application_tracker_requires_authentication(client):
    response = client.get("/applications")

    assert response.status_code == 401
