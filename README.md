# Mini Job Portal

A full-stack job search and recruitment portfolio project built with FastAPI,
PostgreSQL, and Vanilla JavaScript. It demonstrates REST API development,
authentication, role-based authorization, automated testing, and cloud deployment.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST_API-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/pytest-51_passed-0A9EDC?logo=pytest&logoColor=white)](#automated-testing)
[![Coverage](https://img.shields.io/badge/coverage-75%25-brightgreen)](#automated-testing)

- **Live demo:** [mini-job-portal.pages.dev](https://mini-job-portal.pages.dev)
- **Backend API:** [mini-job-portal-api.onrender.com](https://mini-job-portal-api.onrender.com)
- **Swagger UI:** [mini-job-portal-api.onrender.com/docs](https://mini-job-portal-api.onrender.com/docs)

> The backend runs on Render's free service and may need a short cold start after
> a period of inactivity.

![Mini Job Portal job discovery](docs/screenshots/02-jobs.png)

*Production job discovery with keyword, category, location, salary, sorting, and
pagination controls.*

## Project Overview

Mini Job Portal supports two user roles: candidates discover jobs and manage their
applications, while administrators manage categories, jobs, and application
statuses. The project covers a complete recruitment workflow without adding an
employer or company-account role.

The frontend and REST API are deployed separately, with data stored in Supabase
PostgreSQL. A 51-test backend suite verifies authentication, authorization,
business rules, API behavior, and deletion regressions without accessing
production services.

## Features

### Candidate

- Register and log in with a candidate account
- Browse jobs and view job details
- Search by job title or company
- Filter by category, location, and salary range
- Sort and paginate job results
- Apply to a job once
- View only their own applications and current statuses
- Withdraw a pending application

### Admin

- Log in through the same authentication API with the admin role
- View dashboard totals, recent jobs, and recent applications
- Create and delete categories
- Create, update, and delete jobs
- View all applications and individual application details
- Change an application status to pending, accepted, or rejected
- Use admin-only operations protected by role-based access control (RBAC)

## Tech Stack

| Area | Technologies |
| --- | --- |
| Frontend | HTML5, CSS3, Vanilla JavaScript, Fetch API |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL, Supabase |
| Authentication | JWT (`python-jose`), Passlib, bcrypt |
| Testing | pytest, FastAPI TestClient, SQLite, pytest-cov |
| Deployment | Cloudflare Pages, Render, Supabase |
| Development | Git, GitHub, Swagger UI |

## System Architecture

```mermaid
flowchart LR
    U[Candidate or Admin Browser]
    F[Vanilla JS Frontend<br/>Cloudflare Pages]
    API[FastAPI REST API<br/>Render]
    AUTH[JWT Authentication<br/>and RBAC]
    ORM[SQLAlchemy ORM]
    DB[(Supabase PostgreSQL)]

    U --> F
    F -->|HTTPS / JSON| API
    API --> AUTH
    AUTH --> ORM
    ORM --> DB
```

The browser loads the static frontend from Cloudflare Pages. JavaScript sends
JSON requests to FastAPI, which applies authentication, authorization, and
business validation before SQLAlchemy accesses PostgreSQL.

### Example request flow

```text
Candidate browser -> Vanilla JavaScript -> POST /jobs/{id}/apply
-> JWT validation -> Candidate role and duplicate checks
-> SQLAlchemy -> PostgreSQL -> JSON response
```

## Database Design

```mermaid
erDiagram
    USERS ||--o{ APPLICATIONS : submits
    CATEGORIES ||--o{ JOBS : contains
    JOBS ||--o{ APPLICATIONS : receives

    USERS {
        int id PK
        string full_name
        string email UK
        string password_hash
        string role
    }
    CATEGORIES {
        int id PK
        string name UK
    }
    JOBS {
        int id PK
        int category_id FK
        string title
        string company
        string location
        int salary_min
        int salary_max
    }
    APPLICATIONS {
        int id PK
        int user_id FK
        int job_id FK
        string status
    }
```

Each application belongs to one user and one job. A unique constraint on
`(user_id, job_id)` prevents duplicate applications at the database level. The
API blocks deletion of a job that has applications and deletion of a category
that is still used by a job.

## Authentication & Authorization

- Passwords are hashed with Passlib and bcrypt before storage.
- Successful login returns a time-limited JWT used as a Bearer token.
- New public registrations always receive the `candidate` role.
- Admin routes require an authenticated user with the `admin` role.
- Candidate application routes require the `candidate` role.
- Candidate queries include ownership checks, so candidates cannot view or
  withdraw another candidate's application.
- Protected routes return `401` when authentication is missing or invalid and
  `403` when the authenticated role lacks permission.

No production tokens, passwords, or secret-key values are stored in this
repository. Automated tests use only local fake credentials.

## Important Business Rules

- A candidate cannot perform admin operations.
- Public registration cannot create an admin account.
- A candidate can apply to the same job only once.
- A candidate can access only their own private application records.
- Only a pending application can be withdrawn.
- Accepted and rejected applications cannot be withdrawn.
- Only an admin can update application status.
- A job with any application cannot be deleted and returns `409 Conflict`.
- A category containing a job cannot be deleted and returns `409 Conflict`.
- Job salary ranges must be non-negative and the maximum cannot be below the
  minimum.

## REST API

Detailed request and response schemas are available in the
[production Swagger UI](https://mini-job-portal-api.onrender.com/docs).

### Health

| Method | Endpoint | Access | Description |
| --- | --- | --- | --- |
| GET | `/` | Public | API status message |
| GET | `/health` | Public | Application health check |
| GET | `/health/db` | Public | Database connectivity check |

### Authentication

| Method | Endpoint | Access | Description |
| --- | --- | --- | --- |
| POST | `/auth/register` | Public | Register a candidate |
| POST | `/auth/login` | Public | Authenticate and receive a JWT |
| GET | `/auth/me` | Authenticated | Return the current user |

### Categories

| Method | Endpoint | Access | Description |
| --- | --- | --- | --- |
| GET | `/categories` | Public | List categories |
| POST | `/categories` | Admin | Create a category |
| DELETE | `/categories/{category_id}` | Admin | Delete an unused category |

### Jobs

| Method | Endpoint | Access | Description |
| --- | --- | --- | --- |
| GET | `/jobs` | Public | Search, filter, sort, and paginate jobs |
| GET | `/jobs/meta/locations` | Public | List available job locations |
| GET | `/jobs/{job_id}` | Public | Get job details |
| POST | `/jobs` | Admin | Create a job |
| PUT | `/jobs/{job_id}` | Admin | Update a job |
| DELETE | `/jobs/{job_id}` | Admin | Delete a job without applications |

### Applications

| Method | Endpoint | Access | Description |
| --- | --- | --- | --- |
| POST | `/jobs/{job_id}/apply` | Candidate | Apply to a job |
| GET | `/applications/me` | Candidate | List own applications |
| GET | `/applications/me/{application_id}` | Candidate | View one owned application |
| DELETE | `/applications/me/{application_id}` | Candidate | Withdraw a pending application |
| GET | `/admin/applications` | Admin | List all applications |
| GET | `/admin/applications/{application_id}` | Admin | View application details |
| PATCH | `/admin/applications/{application_id}/status` | Admin | Update application status |

### Admin Dashboard

| Method | Endpoint | Access | Description |
| --- | --- | --- | --- |
| GET | `/admin/dashboard` | Admin | View summary totals |
| GET | `/admin/dashboard/recent-applications` | Admin | View recent applications |
| GET | `/admin/dashboard/recent-jobs` | Admin | View recent jobs |

## Project Structure

```text
mini-job-portal/
|-- app/
|   |-- core/                  # JWT and password security helpers
|   |-- dependencies/          # Authentication and RBAC dependencies
|   |-- models/                # SQLAlchemy database models
|   |-- routers/               # FastAPI REST endpoints
|   |-- schemas/               # Pydantic request/response schemas
|   |-- cleanup_verification_data.py
|   |-- create_admin.py        # Secure CLI admin creation
|   |-- database.py
|   |-- init_db.py
|   `-- main.py
|-- frontend/
|   |-- css/
|   |-- js/
|   |-- admin.html
|   |-- applications.html
|   |-- index.html
|   |-- job-detail.html
|   |-- jobs.html
|   |-- login.html
|   `-- register.html
|-- tests/
|   |-- conftest.py
|   |-- test_admin.py
|   |-- test_applications.py
|   |-- test_auth.py
|   |-- test_health.py
|   `-- test_jobs.py
|-- .env.example
|-- .gitignore
|-- requirements.txt
|-- requirements-dev.txt
`-- README.md
```

## Automated Testing

Phase 9.1 established the following verified result:

| Metric | Result |
| --- | ---: |
| Tests | 51 |
| Passed | 51 |
| Failed | 0 |
| Skipped | 0 |
| Coverage | 75% |

The suite covers health endpoints, authentication, JWT behavior, RBAC,
categories, job CRUD, search/filter/sort/pagination, applications, status
updates, withdrawal rules, and deletion integrity.

Tests use an isolated SQLite in-memory database with `StaticPool` and a FastAPI
dependency override. Safety assertions require both test and application engines
to use SQLite. The suite does not call Supabase or Render and does not create
production records.

A key regression test verifies that deleting a job with a pending, accepted, or
rejected application returns `409 Conflict` instead of an unexpected server
error, while preserving both records.

### Run tests

```powershell
python -m pip install -r requirements-dev.txt
pytest -v
pytest --cov=app --cov-report=term-missing
```

## Running Locally

### 1. Clone and create the virtual environment

```powershell
git clone https://github.com/VoPhiToan/mini-job-portal.git
cd mini-job-portal
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Configure the environment

Copy `.env.example` to `.env`, then replace the placeholders with your own local
or development values. Never commit `.env`.

```powershell
Copy-Item .env.example .env
```

### 3. Start the backend

```powershell
uvicorn app.main:app --reload --port 8002
```

- API: [http://127.0.0.1:8002](http://127.0.0.1:8002)
- Swagger UI: [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs)

### 4. Start the frontend

For local full-stack development, set `API_BASE_URL` in `frontend/js/config.js`
to `http://127.0.0.1:8002`. Then start a simple static server:

```powershell
cd frontend
python -m http.server 5500
```

Open [http://127.0.0.1:5500](http://127.0.0.1:5500). The backend CORS settings
allow this local frontend origin.

## Environment Variables

| Variable | Required | Purpose | Safe example |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | SQLAlchemy PostgreSQL connection string | `postgresql+psycopg2://USER:PASSWORD@HOST:PORT/postgres` |
| `JWT_SECRET_KEY` | Yes | Signs and validates JWTs | `replace-with-a-long-random-secret` |
| `JWT_ALGORITHM` | Yes | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | Positive JWT lifetime in minutes | `60` |

## Deployment

- **Frontend:** Cloudflare Pages at
  [mini-job-portal.pages.dev](https://mini-job-portal.pages.dev)
- **Backend:** Render at
  [mini-job-portal-api.onrender.com](https://mini-job-portal-api.onrender.com)
- **Database:** Supabase PostgreSQL

The frontend calls the deployed REST API over HTTPS. Runtime secrets and database
connection settings are configured through the hosting provider's environment
variables and are not stored in source control.

### Production health checks

- `GET /health` confirms that the FastAPI application is running.
- `GET /health/db` performs a minimal database connectivity check without
  exposing database internals.

## Security Practices

- JWT-based authentication with expiring access tokens
- Passlib/bcrypt password hashing
- Candidate/Admin RBAC dependencies on protected routes
- Ownership checks for candidate application records
- Exact production and local CORS origin allowlist
- Environment-based secret and database configuration
- `.env`, virtual environments, caches, coverage output, and test databases ignored
  by Git
- Database uniqueness constraints and API-level deletion integrity checks
- Fully isolated SQLite test database with production-access safeguards
- Explicitly marked cleanup tooling for temporary production verification data

## Engineering Highlights

- Designed REST endpoints and relational models for candidate and admin workflows.
- Implemented JWT authentication and role-based route protection.
- Added ownership and integrity rules for private applications and linked records.
- Built 51 automated backend tests with 75% code coverage.
- Isolated automated tests from production through SQLite and dependency overrides.
- Deployed the frontend, backend, and database across Cloudflare, Render, and
  Supabase.
- Performed authenticated browser E2E checks and production regression verification.

## Screenshots

### Job Discovery

![Mini Job Portal Home](docs/screenshots/01-home.png)

The production landing page introduces the candidate workflow and provides a
focused job search entry point.

![Job Detail](docs/screenshots/03-job-detail.png)

Candidate-facing job details present the role, salary range, location,
description, and application entry point.

### Candidate Experience

![Candidate Applications](docs/screenshots/04-candidate-applications.png)

Candidates can track application status, inspect details, and withdraw a pending
application.

### Admin Experience

![Admin Dashboard](docs/screenshots/05-admin-dashboard.png)

The dashboard summarizes users, jobs, categories, applications, statuses, and
recent activity.

![Admin Job Management](docs/screenshots/06-admin-jobs.png)

Administrators manage categories and job listings through dedicated create,
edit, and delete controls.

![Admin Applications](docs/screenshots/07-admin-applications.png)

The application review workspace connects candidate, job, date, and status
management in one view.

### REST API

![Swagger API Documentation](docs/screenshots/08-swagger.png)

The deployed FastAPI Swagger UI exposes the REST endpoint groups and OpenAPI
schemas without an authorization token.

## Known Limitations

- Render's free service can have cold-start delays.
- No email verification or password-reset workflow is implemented.
- The project has Candidate and Admin roles, but no separate employer/company role.
- CV/resume upload is not implemented.
- Automated tests run locally; a CI pipeline is not configured yet.
- Database schema changes are not managed with a migration tool yet.

## Future Improvements

- Add GitHub Actions for automated tests and coverage checks.
- Add email verification and a secure password-reset flow.
- Add CV/resume upload with file validation and safe storage.
- Add an employer/company workflow with carefully designed permissions.
- Add advanced search options and saved filters.
- Add Alembic database migrations and containerized local development.
- Expand error-path and service-failure tests.

## Portfolio Scope

Mini Job Portal is a learning and portfolio project. It demonstrates full-stack
integration, backend API development, relational database modeling,
authentication, authorization, automated testing, debugging, deployment, and
production verification.
