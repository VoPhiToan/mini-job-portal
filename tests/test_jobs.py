from datetime import datetime, timedelta, timezone

from app.models import Category, Job


def add_job(db, category, **overrides):
    values = {
        "title": "Backend Engineer",
        "company": "Alpha Labs",
        "location": "Ho Chi Minh City",
        "salary_min": 1000,
        "salary_max": 2000,
        "description": "Backend role",
        "category_id": category.id,
    }
    values.update(overrides)
    record = Job(**values)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_public_job_list_and_detail(client, job):
    listing = client.get("/jobs")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    detail = client.get(f"/jobs/{job.id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == job.id


def test_missing_job_returns_404(client):
    assert client.get("/jobs/9999").status_code == 404


def test_keyword_search_matches_title_and_company(client, db_session, category):
    add_job(db_session, category, title="Python API Engineer", company="Alpha Labs")
    add_job(db_session, category, title="Frontend Engineer", company="Beta Python Co")
    add_job(db_session, category, title="Java Engineer", company="Gamma")
    response = client.get("/jobs", params={"search": "python"})
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_category_filter(client, db_session, category):
    other = Category(name="Design")
    db_session.add(other)
    db_session.commit()
    add_job(db_session, category)
    add_job(db_session, other, title="Product Designer")
    response = client.get("/jobs", params={"category_id": category.id})
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["category_id"] == category.id


def test_location_filter(client, db_session, category):
    add_job(db_session, category, location="Ha Noi")
    add_job(db_session, category, title="Remote Engineer", location="Remote")
    response = client.get("/jobs", params={"location": "ha noi"})
    assert response.json()["total"] == 1


def test_salary_filters_use_range_overlap(client, db_session, category):
    add_job(db_session, category, title="Junior", salary_min=500, salary_max=1000)
    add_job(db_session, category, title="Middle", salary_min=1500, salary_max=2500)
    add_job(db_session, category, title="Senior", salary_min=3000, salary_max=5000)
    minimum = client.get("/jobs", params={"salary_min": 2000}).json()
    maximum = client.get("/jobs", params={"salary_max": 1200}).json()
    overlap = client.get(
        "/jobs", params={"salary_min": 900, "salary_max": 1600}
    ).json()
    assert {item["title"] for item in minimum["items"]} == {"Middle", "Senior"}
    assert {item["title"] for item in maximum["items"]} == {"Junior"}
    assert {item["title"] for item in overlap["items"]} == {"Junior", "Middle"}


def test_invalid_salary_filter_returns_422(client):
    assert (
        client.get("/jobs", params={"salary_min": 2000, "salary_max": 1000}).status_code
        == 422
    )


def test_sorting_and_pagination(client, db_session, category):
    now = datetime.now(timezone.utc)
    oldest = add_job(
        db_session, category, title="Oldest", salary_min=3000, salary_max=4000,
        created_at=now - timedelta(days=2)
    )
    add_job(
        db_session, category, title="Middle", salary_min=1000, salary_max=2000,
        created_at=now - timedelta(days=1)
    )
    newest = add_job(
        db_session, category, title="Newest", salary_min=2000, salary_max=3000,
        created_at=now
    )
    assert client.get("/jobs", params={"sort": "oldest"}).json()["items"][0]["id"] == oldest.id
    assert client.get("/jobs", params={"sort": "newest"}).json()["items"][0]["id"] == newest.id
    assert client.get("/jobs", params={"sort": "salary_asc"}).json()["items"][0]["title"] == "Middle"
    page = client.get("/jobs", params={"sort": "oldest", "skip": 1, "limit": 1}).json()
    assert page["total"] == 3
    assert len(page["items"]) == 1
    assert page["skip"] == 1


def test_locations_metadata_is_unique_and_sorted(client, db_session, category):
    add_job(db_session, category, location="Remote")
    add_job(db_session, category, title="Second", location="Da Nang")
    add_job(db_session, category, title="Third", location="Remote")
    response = client.get("/jobs/meta/locations")
    assert response.status_code == 200
    assert response.json() == ["Da Nang", "Remote"]
