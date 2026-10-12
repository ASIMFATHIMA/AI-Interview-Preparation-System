"""
End-to-End Integration Test for Milestone 1.3 - Complete Student Profile & Resume Lifecycle.
Tests full pipeline: Register -> Login -> Profile Edit -> Resume Upload -> Validation -> Multi-tenant Isolation -> Deletion.
"""
import io
import os
import pytest
from app.models.student import Student
from app.models.resume import Resume


def test_complete_m1_3_e2e_workflow(client, db_session):
    print("\n" + "=" * 70)
    print("STARTING COMPLETE E2E WORKFLOW TEST FOR MILESTONE 1.3")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. AUTHENTICATION TESTS
    # -------------------------------------------------------------
    print("\n[STEP 1] Testing Student Registration...")
    reg_payload = {
        "name": "Sarah Connor",
        "email": "sarah.connor@cyberdyne.io",
        "password": "StrongPassword123!",
    }
    reg_resp = client.post("/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    student_a_data = reg_resp.json()
    student_a_id = student_a_data["student_id"]
    assert student_a_data["name"] == "Sarah Connor"
    assert student_a_data["email"] == "sarah.connor@cyberdyne.io"
    assert "password_hash" not in student_a_data
    print(f" -> Student A registered successfully with ID: {student_a_id}")

    print("\n[STEP 2] Testing Duplicate Email Rejection...")
    dup_resp = client.post("/auth/register", json=reg_payload)
    assert dup_resp.status_code == 400
    assert "already registered" in dup_resp.json()["detail"].lower()
    print(" -> Duplicate registration correctly rejected with 400 Bad Request.")

    print("\n[STEP 3] Testing Incorrect Password Login...")
    bad_login_resp = client.post(
        "/auth/login",
        json={"email": "sarah.connor@cyberdyne.io", "password": "WrongPassword999!"},
    )
    assert bad_login_resp.status_code == 401
    assert "invalid email or password" in bad_login_resp.json()["detail"].lower()
    print(" -> Incorrect password rejected with 401 Unauthorized.")

    print("\n[STEP 4] Testing Valid Student Login & JWT Token Generation...")
    login_resp = client.post(
        "/auth/login",
        json={"email": "sarah.connor@cyberdyne.io", "password": "StrongPassword123!"},
    )
    assert login_resp.status_code == 200
    token_a = login_resp.json()["access_token"]
    assert len(token_a) > 20
    auth_headers_a = {"Authorization": f"Bearer {token_a}"}
    print(f" -> JWT Bearer token issued: {token_a[:25]}...")

    print("\n[STEP 5] Testing Protected Endpoint Without JWT...")
    unauth_resp = client.get("/profile/me")
    assert unauth_resp.status_code == 401
    print(" -> Protected endpoint correctly returned 401 for unauthenticated request.")

    # -------------------------------------------------------------
    # 2. PROFILE MODULE TESTS
    # -------------------------------------------------------------
    print("\n[STEP 6] Fetching Student Profile (GET /profile/me)...")
    profile_resp = client.get("/profile/me", headers=auth_headers_a)
    assert profile_resp.status_code == 200
    profile_data = profile_resp.json()
    assert profile_data["email"] == "sarah.connor@cyberdyne.io"
    assert profile_data["degree"] is None
    print(" -> Initial profile fetched successfully.")

    print("\n[STEP 7] Updating Student Profile (PUT /profile/me)...")
    update_payload = {
        "name": "Sarah Connor",
        "phone": "9876543210",
        "location": "Los Angeles, CA",
        "degree": "B.Tech",
        "field_of_study": "Artificial Intelligence & Data Science",
        "institution": "MIT World Peace University",
        "github_url": "https://github.com/sarahconnor",
        "linkedin_url": "https://linkedin.com/in/sarahconnor",
        "portfolio_url": "https://sarahconnor.ai",
    }
    put_resp = client.put("/profile/me", headers=auth_headers_a, json=update_payload)
    assert put_resp.status_code == 200
    updated_profile = put_resp.json()
    assert updated_profile["phone"] == "9876543210"
    assert updated_profile["location"] == "Los Angeles, CA"
    assert updated_profile["degree"] == "B.Tech"
    assert updated_profile["field_of_study"] == "Artificial Intelligence & Data Science"
    assert updated_profile["institution"] == "MIT World Peace University"
    assert updated_profile["github_url"] == "https://github.com/sarahconnor"
    assert updated_profile["linkedin_url"] == "https://linkedin.com/in/sarahconnor"
    assert updated_profile["portfolio_url"] == "https://sarahconnor.ai"
    print(" -> Profile updated successfully and validated against returned schema.")

    # -------------------------------------------------------------
    # 3. RESUME UPLOAD & VALIDATION TESTS
    # -------------------------------------------------------------
    print("\n[STEP 8] Uploading Valid PDF Resume (POST /resume/upload)...")
    pdf_bytes = b"%PDF-1.4 Mock Sarah Connor Resume for AI Research and Data Science"
    upload_pdf_resp = client.post(
        "/resume/upload",
        headers=auth_headers_a,
        files={"file": ("sarah_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_pdf_resp.status_code == 201
    pdf_data = upload_pdf_resp.json()
    assert pdf_data["success"] is True
    resume_1 = pdf_data["resume"]
    resume_1_id = resume_1["resume_id"]
    assert resume_1["original_name"] == "sarah_resume.pdf"
    assert resume_1["file_type"] == "PDF"
    assert resume_1["file_size"] == len(pdf_bytes)
    assert resume_1["status"] == "uploaded"
    print(f" -> PDF Resume uploaded successfully with Resume ID #{resume_1_id}.")

    print("\n[STEP 9] Uploading Valid DOCX Resume (POST /resume/upload)...")
    docx_bytes = b"PK\x03\x04 Mock DOCX Resume binary payload"
    upload_docx_resp = client.post(
        "/resume/upload",
        headers=auth_headers_a,
        files={"file": ("sarah_cv.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert upload_docx_resp.status_code == 201
    resume_2 = upload_docx_resp.json()["resume"]
    resume_2_id = resume_2["resume_id"]
    assert resume_2["file_type"] == "DOCX"
    print(f" -> DOCX Resume uploaded successfully with Resume ID #{resume_2_id}.")

    print("\n[STEP 10] Testing Rejection of Invalid File Formats (.jpg, .png, .exe)...")
    for bad_file, bad_mime in [
        ("photo.jpg", "image/jpeg"),
        ("avatar.png", "image/png"),
        ("script.exe", "application/x-msdownload"),
    ]:
        bad_resp = client.post(
            "/resume/upload",
            headers=auth_headers_a,
            files={"file": (bad_file, io.BytesIO(b"bad content"), bad_mime)},
        )
        assert bad_resp.status_code == 400
        assert "Only PDF and DOCX files are allowed" in bad_resp.json()["detail"]
    print(" -> All invalid file formats correctly rejected with 400 Bad Request.")

    print("\n[STEP 11] Testing Rejection of Oversized File (> 5 MB)...")
    huge_bytes = b"X" * (5 * 1024 * 1024 + 1024)  # 5 MB + 1 KB
    huge_resp = client.post(
        "/resume/upload",
        headers=auth_headers_a,
        files={"file": ("huge.pdf", io.BytesIO(huge_bytes), "application/pdf")},
    )
    assert huge_resp.status_code == 400
    assert "exceeds maximum allowed size of 5 MB" in huge_resp.json()["detail"]
    print(" -> Oversized file (> 5 MB) correctly rejected with 400 Bad Request.")

    print("\n[STEP 12] Listing and Inspecting Resumes (GET /resume and GET /resume/{id})...")
    list_resp = client.get("/resume", headers=auth_headers_a)
    assert list_resp.status_code == 200
    resume_list = list_resp.json()
    assert len(resume_list) == 2
    
    get_single_resp = client.get(f"/resume/{resume_1_id}", headers=auth_headers_a)
    assert get_single_resp.status_code == 200
    single_metadata = get_single_resp.json()
    assert single_metadata["original_name"] == "sarah_resume.pdf"
    assert single_metadata["stored_name"] != "sarah_resume.pdf"  # Stored name is unique UUID
    print(f" -> Successfully listed {len(resume_list)} resumes and verified stored UUID name.")

    # -------------------------------------------------------------
    # 4. MULTI-TENANT ISOLATION TESTS
    # -------------------------------------------------------------
    print("\n[STEP 13] Testing Multi-Tenant Security & Isolation...")
    # Register Student B
    client.post(
        "/auth/register",
        json={"name": "John Connor", "email": "john.connor@resistance.net", "password": "Password123!"},
    )
    token_b = client.post(
        "/auth/login",
        json={"email": "john.connor@resistance.net", "password": "Password123!"},
    ).json()["access_token"]
    auth_headers_b = {"Authorization": f"Bearer {token_b}"}

    # Student B queries their own profile
    b_profile = client.get("/profile/me", headers=auth_headers_b).json()
    assert b_profile["email"] == "john.connor@resistance.net"
    assert b_profile["location"] is None  # Student A's location was LA, Student B is clean

    # Student B attempts to access Student A's resume -> 404
    b_access_resp = client.get(f"/resume/{resume_1_id}", headers=auth_headers_b)
    assert b_access_resp.status_code == 404

    # Student B attempts to delete Student A's resume -> 404
    b_delete_resp = client.delete(f"/resume/{resume_1_id}", headers=auth_headers_b)
    assert b_delete_resp.status_code == 404
    print(" -> Verified strict isolation: Student B cannot view or modify Student A's data.")

    # -------------------------------------------------------------
    # 5. RESUME DELETION & M1.4 PARSE PLACEHOLDER TESTS
    # -------------------------------------------------------------
    print("\n[STEP 14] Testing M1.4 Parse Placeholder Endpoint (POST /resume/{id}/parse)...")
    parse_resp = client.post(f"/resume/{resume_1_id}/parse", headers=auth_headers_a)
    assert parse_resp.status_code == 200
    assert parse_resp.json()["success"] is True
    assert "Failed to extract text from PDF" in parse_resp.json()["message"]
    print(" -> Milestone 1.4 parse placeholder endpoint successfully verified.")

    print("\n[STEP 15] Testing Resume Deletion (DELETE /resume/{id})...")
    del_resp = client.delete(f"/resume/{resume_1_id}", headers=auth_headers_a)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Confirm resume is gone
    confirm_del_resp = client.get(f"/resume/{resume_1_id}", headers=auth_headers_a)
    assert confirm_del_resp.status_code == 404
    print(f" -> Resume #{resume_1_id} deleted and confirmed inaccessible (404).")

    print("\n" + "=" * 70)
    print("ALL MILESTONE 1.3 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
