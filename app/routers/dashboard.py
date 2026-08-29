from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.application import Application
from app.models.category import Category
from app.models.job import Job
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary,
    RecentApplicationResponse,
    RecentJobResponse,
)


router = APIRouter(prefix="/admin/dashboard", tags=["Dashboard"])


def count_rows(db: Session, column) -> int:
    return db.query(func.count(column)).scalar() or 0


@router.get("", response_model=DashboardSummary)
def get_dashboard_summary(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    return DashboardSummary(
        total_users=count_rows(db, User.id),
        total_candidates=(
            db.query(func.count(User.id)).filter(User.role == "candidate").scalar() or 0
        ),
        total_admins=(
            db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0
        ),
        total_jobs=count_rows(db, Job.id),
        total_categories=count_rows(db, Category.id),
        total_applications=count_rows(db, Application.id),
        pending_applications=(
            db.query(func.count(Application.id))
            .filter(Application.status == "pending")
            .scalar()
            or 0
        ),
        accepted_applications=(
            db.query(func.count(Application.id))
            .filter(Application.status == "accepted")
            .scalar()
            or 0
        ),
        rejected_applications=(
            db.query(func.count(Application.id))
            .filter(Application.status == "rejected")
            .scalar()
            or 0
        ),
    )


@router.get(
    "/recent-applications",
    response_model=list[RecentApplicationResponse],
)
def get_recent_applications(
    limit: int = Query(default=5, ge=1, le=20),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[RecentApplicationResponse]:
    applications = (
        db.query(Application)
        .options(joinedload(Application.user), joinedload(Application.job))
        .order_by(Application.created_at.desc(), Application.id.desc())
        .limit(limit)
        .all()
    )
    return [
        RecentApplicationResponse(
            id=application.id,
            status=application.status,
            created_at=application.created_at,
            candidate_id=application.user.id,
            candidate_full_name=application.user.full_name,
            candidate_email=application.user.email,
            job_id=application.job.id,
            job_title=application.job.title,
            company=application.job.company,
        )
        for application in applications
    ]


@router.get("/recent-jobs", response_model=list[RecentJobResponse])
def get_recent_jobs(
    limit: int = Query(default=5, ge=1, le=20),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Job]:
    return (
        db.query(Job)
        .options(joinedload(Job.category))
        .order_by(Job.created_at.desc(), Job.id.desc())
        .limit(limit)
        .all()
    )
