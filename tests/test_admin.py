from app.models import Category, Job


def job_payload(category_id):
    return {
        "title": "Python Developer",
        "company": "Test Company",
        "location": "Da Nang",
        "salary_min": 1200,
        "salary_max": 2200,
        "description": "Develop testable backend services.",
        "category_id": category_id,
    }


def test_admin_can_create_category(client, admin_headers):
    response = client.post(
        "/categories", json={"name": "Data Engineering"}, headers=admin_headers
    )
    assert response.status_code == 201


def test_duplicate_category_returns_409(client, admin_headers, category):
    response = client.post(
        "/categories", json={"name": category.name}, headers=admin_headers
    )
    assert response.status_code == 409


def test_get_categories_is_public(client, category):
    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json()[0]["id"] == category.id


def test_admin_can_delete_unused_category(client, admin_headers, category):
    response = client.delete(f"/categories/{category.id}", headers=admin_headers)
    assert response.status_code == 204


def test_category_with_job_cannot_be_deleted(client, admin_headers, category, job):
    response = client.delete(f"/categories/{category.id}", headers=admin_headers)
    assert response.status_code == 409


def test_missing_category_delete_returns_404(client, admin_headers):
    assert client.delete("/categories/9999", headers=admin_headers).status_code == 404


def test_candidate_cannot_manage_categories(client, candidate_headers, category):
    assert (
        client.post(
            "/categories", json={"name": "Forbidden"}, headers=candidate_headers
        ).status_code
        == 403
    )
    assert (
        client.delete(f"/categories/{category.id}", headers=candidate_headers).status_code
        == 403
    )


def test_unauthenticated_category_writes_return_401(client, category):
    assert client.post("/categories", json={"name": "Forbidden"}).status_code == 401
    assert client.delete(f"/categories/{category.id}").status_code == 401


def test_admin_dashboard_access(client, admin_headers):
    response = client.get("/admin/dashboard", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["total_admins"] == 1


def test_candidate_cannot_access_admin_dashboard(client, candidate_headers):
    assert client.get("/admin/dashboard", headers=candidate_headers).status_code == 403


def test_unauthenticated_admin_dashboard_returns_401(client):
    assert client.get("/admin/dashboard").status_code == 401


def test_admin_can_create_job(client, admin_headers, category):
    response = client.post(
        "/jobs", json=job_payload(category.id), headers=admin_headers
    )
    assert response.status_code == 201
    assert response.json()["category_name"] == category.name


def test_candidate_and_anonymous_cannot_create_job(
    client, candidate_headers, category
):
    payload = job_payload(category.id)
    assert client.post("/jobs", json=payload, headers=candidate_headers).status_code == 403
    assert client.post("/jobs", json=payload).status_code == 401


def test_admin_can_update_job(client, admin_headers, job):
    response = client.put(
        f"/jobs/{job.id}", json={"title": "Senior Backend Developer"}, headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Senior Backend Developer"


def test_candidate_and_anonymous_cannot_update_or_delete_job(
    client, candidate_headers, job
):
    assert (
        client.put(
            f"/jobs/{job.id}", json={"title": "Forbidden Title"}, headers=candidate_headers
        ).status_code
        == 403
    )
    assert client.put(f"/jobs/{job.id}", json={"title": "No Auth"}).status_code == 401
    assert client.delete(f"/jobs/{job.id}", headers=candidate_headers).status_code == 403
    assert client.delete(f"/jobs/{job.id}").status_code == 401


def test_admin_can_delete_job_without_applications(client, admin_headers, job):
    assert client.delete(f"/jobs/{job.id}", headers=admin_headers).status_code == 204
    assert client.get(f"/jobs/{job.id}").status_code == 404
