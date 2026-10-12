"""
Test suite for Resume Upload and Metadata Storage Module (Milestone 1.3).
Tests PDF/DOCX uploads, rejection of invalid extensions, 5MB size limits,
metadata retrieval, deletion, multi-tenant isolation, and parse placeholder.
"""
import io
import os
from pathlib import Path
import pytest


def get_authenticated_token(client, email="student@example.com", name="Resume Tester"):
    """
    Helper to register and login a student, returning their JWT Bearer token.
    """
    client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": "Password123!"},
    )
    res = client.post(
        "/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return res.json()["access_token"]


def test_1_upload_pdf_success(client):
    """
    Test uploading a valid PDF file.
    """
    token = get_authenticated_token(client, email="pdf_test@example.com")
    pdf_content = b"%PDF-1.4 Mock PDF Content with bytes..."

    response = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("my_resume.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Resume uploaded successfully"
    resume = data["resume"]
    assert resume["original_name"] == "my_resume.pdf"
    assert resume["file_type"] == "PDF"
    assert resume["file_size"] == len(pdf_content)
    assert resume["status"] == "uploaded"
    assert "resume_id" in resume


def test_2_upload_docx_success(client):
    """
    Test uploading a valid DOCX file.
    """
    token = get_authenticated_token(client, email="docx_test@example.com")
    docx_content = b"PK\x03\x04 Mock DOCX Zip binary stream..."

    response = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("candidate_profile.docx", io.BytesIO(docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    resume = data["resume"]
    assert resume["original_name"] == "candidate_profile.docx"
    assert resume["file_type"] == "DOCX"
    assert resume["status"] == "uploaded"


def test_3_reject_jpg_and_png(client):
    """
    Test rejection of unsupported image file extensions (.jpg, .png).
    """
    token = get_authenticated_token(client, email="image_reject@example.com")

    # JPG test
    jpg_res = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("photo.jpg", io.BytesIO(b"\xff\xd8\xff JPEG mock bytes"), "image/jpeg")},
    )
    assert jpg_res.status_code == 400
    assert "Only PDF and DOCX files are allowed" in jpg_res.json()["detail"]

    # PNG test
    png_res = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("avatar.png", io.BytesIO(b"\x89PNG PNG mock bytes"), "image/png")},
    )
    assert png_res.status_code == 400
    assert "Only PDF and DOCX files are allowed" in png_res.json()["detail"]


def test_4_reject_oversized_file(client):
    """
    Test rejection of files exceeding the 5 MB limit.
    """
    token = get_authenticated_token(client, email="oversized_test@example.com")
    # 5.5 MB payload
    large_content = b"0" * (5 * 1024 * 1024 + 500 * 1024)

    response = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("huge_resume.pdf", io.BytesIO(large_content), "application/pdf")},
    )
    assert response.status_code == 400
    assert "exceeds maximum allowed size of 5 MB" in response.json()["detail"]


def test_5_list_and_get_resume_metadata(client):
    """
    Test listing all resumes and fetching specific metadata by ID.
    """
    token = get_authenticated_token(client, email="metadata_viewer@example.com")

    # Upload 2 resumes
    r1 = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("resume_v1.pdf", io.BytesIO(b"%PDF version 1"), "application/pdf")},
    ).json()["resume"]

    r2 = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("resume_v2.docx", io.BytesIO(b"DOCX version 2"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    ).json()["resume"]

    # List resumes
    list_resp = client.get(
        "/resume",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    resumes = list_resp.json()
    assert len(resumes) == 2

    # Get single resume by ID
    get_resp = client.get(
        f"/resume/{r1['resume_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    single = get_resp.json()
    assert single["original_name"] == "resume_v1.pdf"
    assert single["file_type"] == "PDF"
    assert single["stored_name"] != "resume_v1.pdf"  # Unique stored name verification


def test_6_delete_resume(client):
    """
    Test deleting a resume removes its metadata and physical file.
    """
    token = get_authenticated_token(client, email="deleter@example.com")

    upload_resp = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("to_delete.pdf", io.BytesIO(b"%PDF will be deleted"), "application/pdf")},
    ).json()
    resume_id = upload_resp["resume"]["resume_id"]

    # Delete resume
    del_resp = client.delete(
        f"/resume/{resume_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Confirm it's deleted (404)
    get_resp = client.get(
        f"/resume/{resume_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


def test_7_ownership_security_isolation(client):
    """
    Test that Student B cannot view or delete Student A's resume.
    """
    token_a = get_authenticated_token(client, email="student_a@example.com", name="Student A")
    token_b = get_authenticated_token(client, email="student_b@example.com", name="Student B")

    # Student A uploads resume
    resume_a = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("secret_a.pdf", io.BytesIO(b"%PDF student A secret"), "application/pdf")},
    ).json()["resume"]
    resume_a_id = resume_a["resume_id"]

    # Student B tries to fetch Student A's resume -> 404
    b_get = client.get(
        f"/resume/{resume_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_get.status_code == 404

    # Student B tries to delete Student A's resume -> 404
    b_del = client.delete(
        f"/resume/{resume_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_del.status_code == 404


def test_8_parse_placeholder_m1_4(client):
    """
    Test M1.4 parse endpoint POST /resume/{id}/parse.
    With real implementation, re-parsing returns structured data or a parse error message.
    """
    token = get_authenticated_token(client, email="parser_test@example.com")

    resume = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("parse_target.pdf", io.BytesIO(b"%PDF for parser"), "application/pdf")},
    ).json()["resume"]
    resume_id = resume["resume_id"]

    parse_resp = client.post(
        f"/resume/{resume_id}/parse",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert parse_resp.status_code == 200
    body = parse_resp.json()
    assert body["success"] is True
    assert "message" in body


def test_9_upload_sample_persists_structured_profile_data(client):
    """A real sample upload is parsed and available through the candidate profile API."""
    token = get_authenticated_token(client, email="sample_profile@example.com")
    sample_path = Path(__file__).parent / "test_resumes" / "sample1_fresh_graduate.docx"

    upload_response = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                sample_path.name,
                io.BytesIO(sample_path.read_bytes()),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert upload_response.status_code == 201
    parsed = upload_response.json()["parsed"]
    assert parsed["name"] == "Asha Raman"
    assert "Python" in parsed["skills"]
    assert len(parsed["education"]) == 1
    assert len(parsed["projects"]) == 2
    assert len(parsed["certifications"]) == 2
    assert len(parsed["achievements"]) == 2

    profile_response = client.get(
        "/resume-parsed/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_response.status_code == 200
    profile_data = profile_response.json()["data"]
    assert profile_data["name"] == "Asha Raman"
    assert "Python" in profile_data["skills"]
    assert len(profile_data["experience"]) == 0
    assert len(profile_data["projects"]) == 2


def test_10_upload_returns_ids_and_profile_is_owner_scoped(client):
    token_a = get_authenticated_token(client, email="profile_owner@example.com", name="Profile Owner")
    token_b = get_authenticated_token(client, email="profile_other@example.com", name="Profile Other")

    upload = client.post(
        "/resume/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("profile.pdf", io.BytesIO(b"%PDF invalid test content"), "application/pdf")},
    )
    body = upload.json()
    assert upload.status_code == 201
    assert body["candidate_id"]
    assert body["resume_id"] == body["resume"]["resume_id"]

    profile = client.get(
        f"/resume/profile/{body['candidate_id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert profile.status_code == 200
    assert profile.json()["candidate_id"] == body["candidate_id"]

    other_profile = client.get(
        f"/resume/profile/{body['candidate_id']}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert other_profile.status_code == 404
