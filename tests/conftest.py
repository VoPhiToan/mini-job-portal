import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# These values must be set before importing the application. This prevents the
# test process from even constructing an engine from a developer's production URL.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "local-test-key-not-used-outside-pytest"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from app.core.security import hash_password  # noqa: E402
from app.database import Base, engine as application_engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Category, Job, User  # noqa: E402


TEST_DATABASE_URL = "sqlite://"
assert TEST_DATABASE_URL.startswith("sqlite"), "Tests require an isolated SQLite DB"
assert application_engine.url.get_backend_name() == "sqlite", (
    "The application engine must also be isolated from production during tests"
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)

CANDIDATE_PASSWORD = "CandidateTest123!"
ADMIN_PASSWORD = "AdminTest123!"


class RedactedAuthHeaders(dict):
    def __repr__(self) -> str:
        return "<redacted auth headers>"


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def create_user(db, *, name: str, email: str, password: str, role: str) -> User:
    user = User(
        full_name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return RedactedAuthHeaders(
        {"Authorization": f"Bearer {response.json()['access_token']}"}
    )


@pytest.fixture
def candidate(db_session):
    return create_user(
        db_session,
        name="Test Candidate",
        email="candidate@example.com",
        password=CANDIDATE_PASSWORD,
        role="candidate",
    )


@pytest.fixture
def candidate_headers(client, candidate):
    return login_headers(client, candidate.email, CANDIDATE_PASSWORD)


@pytest.fixture
def admin(db_session):
    return create_user(
        db_session,
        name="Test Admin",
        email="admin@example.com",
        password=ADMIN_PASSWORD,
        role="admin",
    )


@pytest.fixture
def admin_headers(client, admin):
    return login_headers(client, admin.email, ADMIN_PASSWORD)


@pytest.fixture
def category(db_session):
    record = Category(name="Software Engineering")
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


@pytest.fixture
def job(db_session, category):
    record = Job(
        title="Backend Developer",
        company="Example Labs",
        location="Remote",
        salary_min=1000,
        salary_max=2000,
        description="Build and maintain APIs.",
        category_id=category.id,
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record
