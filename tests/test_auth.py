from tests.conftest import CANDIDATE_PASSWORD


def registration_payload(**overrides):
    payload = {
        "full_name": "New Candidate",
        "email": "new-candidate@example.com",
        "password": CANDIDATE_PASSWORD,
    }
    payload.update(overrides)
    return payload


def test_register_candidate_success(client):
    response = client.post("/auth/register", json=registration_payload())
    assert response.status_code == 201
    assert response.json()["role"] == "candidate"
    assert "password" not in response.json()


def test_candidate_cannot_self_register_as_admin(client):
    payload = registration_payload(role="admin")
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["role"] == "candidate"


def test_duplicate_registration_returns_409(client):
    assert client.post("/auth/register", json=registration_payload()).status_code == 201
    assert client.post("/auth/register", json=registration_payload()).status_code == 409


def test_invalid_registration_returns_422(client):
    response = client.post(
        "/auth/register",
        json=registration_payload(email="not-an-email", password="short"),
    )
    assert response.status_code == 422


def test_login_valid_credentials(client, candidate):
    response = client.post(
        "/auth/login",
        data={"username": candidate.email, "password": CANDIDATE_PASSWORD},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_invalid_password_returns_401(client, candidate):
    response = client.post(
        "/auth/login",
        data={"username": candidate.email, "password": "WrongPassword123!"},
    )
    assert response.status_code == 401


def test_auth_me_with_valid_token(client, candidate, candidate_headers):
    response = client.get("/auth/me", headers=candidate_headers)
    assert response.status_code == 200
    assert response.json()["id"] == candidate.id


def test_auth_me_without_token_returns_401(client):
    assert client.get("/auth/me").status_code == 401


def test_auth_me_with_invalid_token_returns_401(client):
    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401


def test_auth_me_with_malformed_authorization_returns_401(client):
    response = client.get(
        "/auth/me", headers={"Authorization": "NotBearer malformed"}
    )
    assert response.status_code == 401
