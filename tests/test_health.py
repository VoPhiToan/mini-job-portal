def test_root_returns_running_message(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Mini Job Portal API is running"}


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_uses_test_database(client):
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"database": "connected"}
