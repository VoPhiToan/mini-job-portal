import pytest

from app.models import Application, Job, User
from tests.conftest import CANDIDATE_PASSWORD, create_user, login_headers


def apply(client, job, headers):
    return client.post(f"/jobs/{job.id}/apply", headers=headers)


def test_candidate_can_apply_and_view_private_application(
    client, candidate_headers, job
):
    response = apply(client, job, candidate_headers)
    assert response.status_code == 201
    application_id = response.json()["id"]
    listing = client.get("/applications/me", headers=candidate_headers)
    detail = client.get(
        f"/applications/me/{application_id}", headers=candidate_headers
    )
    assert listing.status_code == 200
    assert listing.json()[0]["job"]["id"] == job.id
    assert detail.status_code == 200


def test_duplicate_application_returns_409(client, candidate_headers, job):
    assert apply(client, job, candidate_headers).status_code == 201
    assert apply(client, job, candidate_headers).status_code == 409


def test_another_candidate_cannot_access_or_withdraw_private_application(
    client, db_session, candidate_headers, job
):
    application_id = apply(client, job, candidate_headers).json()["id"]
    other = create_user(
        db_session,
        name="Other Candidate",
        email="other@example.com",
        password=CANDIDATE_PASSWORD,
        role="candidate",
    )
    other_headers = login_headers(client, other.email, CANDIDATE_PASSWORD)
    assert (
        client.get(
            f"/applications/me/{application_id}", headers=other_headers
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/applications/me/{application_id}", headers=other_headers
        ).status_code
        == 404
    )


def test_pending_application_can_be_withdrawn(client, candidate_headers, job):
    application_id = apply(client, job, candidate_headers).json()["id"]
    response = client.delete(
        f"/applications/me/{application_id}", headers=candidate_headers
    )
    assert response.status_code == 204
    assert client.get("/applications/me", headers=candidate_headers).json() == []


@pytest.mark.parametrize("new_status", ["accepted", "rejected"])
def test_non_pending_application_cannot_be_withdrawn(
    client, candidate_headers, admin_headers, job, new_status
):
    application_id = apply(client, job, candidate_headers).json()["id"]
    update = client.patch(
        f"/admin/applications/{application_id}/status",
        json={"status": new_status},
        headers=admin_headers,
    )
    assert update.status_code == 200
    response = client.delete(
        f"/applications/me/{application_id}", headers=candidate_headers
    )
    assert response.status_code == 409
    detail = client.get(
        f"/applications/me/{application_id}", headers=candidate_headers
    )
    assert detail.json()["status"] == new_status


@pytest.mark.parametrize("new_status", ["accepted", "rejected"])
def test_admin_status_update_is_visible_to_candidate(
    client, candidate_headers, admin_headers, job, new_status
):
    application_id = apply(client, job, candidate_headers).json()["id"]
    response = client.patch(
        f"/admin/applications/{application_id}/status",
        json={"status": new_status},
        headers=admin_headers,
    )
    assert response.status_code == 200
    detail = client.get(
        f"/applications/me/{application_id}", headers=candidate_headers
    )
    assert detail.json()["status"] == new_status


def test_candidate_cannot_update_application_status(
    client, candidate_headers, job
):
    application_id = apply(client, job, candidate_headers).json()["id"]
    response = client.patch(
        f"/admin/applications/{application_id}/status",
        json={"status": "accepted"},
        headers=candidate_headers,
    )
    assert response.status_code == 403


def test_unauthenticated_application_operations_return_401(client, job):
    assert client.post(f"/jobs/{job.id}/apply").status_code == 401
    assert client.get("/applications/me").status_code == 401
    assert client.get("/admin/applications").status_code == 401


@pytest.mark.parametrize("application_status", ["pending", "accepted", "rejected"])
def test_job_with_application_cannot_be_deleted(
    client,
    db_session,
    admin_headers,
    candidate,
    category,
    application_status,
):
    protected_job = Job(
        title=f"Protected {application_status.title()} Job",
        company="Regression Labs",
        location="Remote",
        salary_min=1000,
        salary_max=2000,
        description="Phase 8.1 regression fixture",
        category_id=category.id,
    )
    db_session.add(protected_job)
    db_session.commit()
    db_session.refresh(protected_job)
    application = Application(
        user_id=candidate.id,
        job_id=protected_job.id,
        status=application_status,
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)

    response = client.delete(f"/jobs/{protected_job.id}", headers=admin_headers)

    assert response.status_code == 409
    assert response.status_code != 500
    db_session.expire_all()
    assert db_session.query(Job).filter_by(id=protected_job.id).first() is not None
    assert db_session.query(Application).filter_by(id=application.id).first() is not None
