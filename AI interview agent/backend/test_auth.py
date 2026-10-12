"""
Test suite for Student Registration, Login, and JWT Authentication.
"""

import bcrypt
from app.models.student import Student


def test_1_register_student_success(client):
    """
    Test student registration with valid data.
    """
    response = client.post(
        "/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane.doe@example.com"
    assert "student_id" in data
    assert "password_hash" not in data
    assert "created_at" in data


def test_2_register_duplicate_email(client):
    """
    Test that duplicate email registration returns 400 Bad Request.
    """
    # First registration
    client.post(
        "/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "password": "SecurePassword123!",
        },
    )

    # Duplicate registration attempt
    response = client.post(
        "/auth/register",
        json={
            "name": "Jane Another",
            "email": "jane.doe@example.com",
            "password": "AnotherPassword123!",
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_3_login_correct_password(client):
    """
    Test student login with correct credentials returns valid JWT token.
    """
    # Register student
    client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": "MySecretPassword123!",
        },
    )

    # Login
    response = client.post(
        "/auth/login",
        json={
            "email": "john.doe@example.com",
            "password": "MySecretPassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_bcrypt_hash_is_stored_and_verifies(client, db_session):
    """Registration stores a bcrypt $2b$12$ hash that authenticates unchanged input."""
    password = "Password with spaces!"
    response = client.post(
        "/auth/register",
        json={
            "name": "Whitespace Password",
            "email": "whitespace@example.com",
            "password": password,
        },
    )

    assert response.status_code == 201
    student = db_session.query(Student).filter_by(email="whitespace@example.com").one()
    assert student.password_hash.startswith("$2b$12$")
    assert bcrypt.checkpw(password.encode("utf-8"), student.password_hash.encode("utf-8"))

    login_response = client.post(
        "/auth/login",
        json={"email": "whitespace@example.com", "password": password},
    )
    assert login_response.status_code == 200


def test_4_login_incorrect_password(client):
    """
    Test student login with incorrect password returns 401 Unauthorized.
    """
    # Register student
    client.post(
        "/auth/register",
        json={
            "name": "Alice Smith",
            "email": "alice@example.com",
            "password": "CorrectPassword123!",
        },
    )

    # Login with wrong password
    response = client.post(
        "/auth/login",
        json={
            "email": "alice@example.com",
            "password": "WrongPassword999!",
        },
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_5_verify_jwt_authentication_dependency(client):
    """
    Test JWT Bearer token authentication against protected /auth/me endpoint.
    """
    # 1. Register
    client.post(
        "/auth/register",
        json={
            "name": "Bob Builder",
            "email": "bob@example.com",
            "password": "BobPassword123!",
        },
    )

    # 2. Login to obtain JWT
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "bob@example.com",
            "password": "BobPassword123!",
        },
    )
    token = login_resp.json()["access_token"]

    # 3. Access protected /auth/me with valid Bearer token
    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    student_profile = me_resp.json()
    assert student_profile["email"] == "bob@example.com"
    assert student_profile["name"] == "Bob Builder"
    assert "password_hash" not in student_profile

    # 4. Access protected /auth/me with invalid Bearer token
    invalid_resp = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_fake_jwt_token"},
    )
    assert invalid_resp.status_code == 401

    # 5. Access protected /auth/me without token
    no_token_resp = client.get("/auth/me")
    assert no_token_resp.status_code == 401
