"""
Test suite for Student Profile API (GET /profile/me and PUT /profile/me).
Verifies authentication enforcement, profile updates, and multi-tenant security isolation.
"""


def test_1_get_profile_unauthorized(client):
    """
    Test GET /profile/me without login token returns 401.
    """
    response = client.get("/profile/me")
    assert response.status_code == 401


def test_2_get_profile_authenticated(client):
    """
    Test GET /profile/me with valid JWT returns student's own profile.
    """
    # 1. Register student
    client.post(
        "/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "Password123!",
        },
    )

    # 2. Login
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "jane@example.com",
            "password": "Password123!",
        },
    )
    token = login_resp.json()["access_token"]

    # 3. Get profile
    profile_resp = client.get(
        "/profile/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_resp.status_code == 200
    data = profile_resp.json()
    assert data["email"] == "jane@example.com"
    assert data["name"] == "Jane Doe"
    assert "password_hash" not in data


def test_3_update_profile_success(client):
    """
    Test PUT /profile/me allows updating profile details.
    """
    # Register & Login
    client.post(
        "/auth/register",
        json={
            "name": "Student One",
            "email": "student1@example.com",
            "password": "Password123!",
        },
    )
    login_resp = client.post(
        "/auth/login",
        json={
            "email": "student1@example.com",
            "password": "Password123!",
        },
    )
    token = login_resp.json()["access_token"]

    # Update profile
    update_payload = {
        "name": "Student One Updated",
        "phone": "9876543210",
        "location": "Chennai",
        "degree": "B.Tech",
        "field_of_study": "Artificial Intelligence and Data Science",
        "institution": "ABC College",
        "github_url": "https://github.com/student1",
        "linkedin_url": "https://linkedin.com/in/student1",
        "portfolio_url": "https://student1.dev",
    }

    put_resp = client.put(
        "/profile/me",
        headers={"Authorization": f"Bearer {token}"},
        json=update_payload,
    )
    assert put_resp.status_code == 200
    updated_data = put_resp.json()

    assert updated_data["name"] == "Student One Updated"
    assert updated_data["phone"] == "9876543210"
    assert updated_data["location"] == "Chennai"
    assert updated_data["degree"] == "B.Tech"
    assert updated_data["field_of_study"] == "Artificial Intelligence and Data Science"
    assert updated_data["institution"] == "ABC College"
    assert updated_data["github_url"] == "https://github.com/student1"
    assert updated_data["linkedin_url"] == "https://linkedin.com/in/student1"
    assert updated_data["portfolio_url"] == "https://student1.dev"

    # Verify persistent retrieval via GET /profile/me
    get_resp = client.get(
        "/profile/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    persisted_data = get_resp.json()
    assert persisted_data["name"] == "Student One Updated"
    assert persisted_data["location"] == "Chennai"
    assert persisted_data["institution"] == "ABC College"
    assert persisted_data["phone"] == "9876543210"


def test_4_multi_tenant_isolation(client):
    """
    Verify that Student A and Student B cannot access or modify each other's profiles.
    """
    # 1. Register Student A
    client.post(
        "/auth/register",
        json={"name": "Student A", "email": "studenta@example.com", "password": "PasswordA123!"},
    )
    token_a = client.post(
        "/auth/login",
        json={"email": "studenta@example.com", "password": "PasswordA123!"},
    ).json()["access_token"]

    # 2. Register Student B
    client.post(
        "/auth/register",
        json={"name": "Student B", "email": "studentb@example.com", "password": "PasswordB123!"},
    )
    token_b = client.post(
        "/auth/login",
        json={"email": "studentb@example.com", "password": "PasswordB123!"},
    ).json()["access_token"]

    # 3. Student A updates their own profile
    client.put(
        "/profile/me",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"location": "San Francisco", "institution": "Stanford University"},
    )

    # 4. Student B queries /profile/me -> receives ONLY Student B's profile
    profile_b = client.get(
        "/profile/me",
        headers={"Authorization": f"Bearer {token_b}"},
    ).json()
    assert profile_b["email"] == "studentb@example.com"
    assert profile_b["name"] == "Student B"
    assert profile_b["location"] is None
    assert profile_b["institution"] is None

    # 5. Student B updates their own profile -> does not affect Student A
    client.put(
        "/profile/me",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"location": "London", "institution": "Imperial College"},
    )

    # 6. Verify Student A's profile remains untouched
    profile_a = client.get(
        "/profile/me",
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()
    assert profile_a["email"] == "studenta@example.com"
    assert profile_a["location"] == "San Francisco"
    assert profile_a["institution"] == "Stanford University"
