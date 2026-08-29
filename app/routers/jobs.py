from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.category import Category
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.schemas.pagination import JobPaginatedResponse


router = APIRouter(prefix="/jobs", tags=["Jobs"])


def get_job_or_404(job_id: int, db: Session) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


def ensure_category_exists(category_id: int, db: Session) -> None:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )


def ensure_valid_salary_range(
    salary_min: int | None,
    salary_max: int | None,
) -> None:
    if (
        salary_min is not None
        and salary_max is not None
        and salary_max < salary_min
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="salary_max must be greater than or equal to salary_min",
        )


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_job(job_data: JobCreate, db: Session = Depends(get_db)) -> Job:
    ensure_category_exists(job_data.category_id, db)
    job = Job(**job_data.model_dump())

    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        ) from exc

    return job


@router.get("", response_model=JobPaginatedResponse)
def get_jobs(
    search: str | None = Query(default=None),
    category_id: int | None = Query(default=None, gt=0),
    location: str | None = Query(default=None),
    salary_min: int | None = Query(default=None, ge=0),
    salary_max: int | None = Query(default=None, ge=0),
    sort: Literal["newest", "oldest", "salary_asc", "salary_desc"] = "newest",
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> JobPaginatedResponse:
    if salary_min is not None and salary_max is not None and salary_max < salary_min:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="salary_max must be greater than or equal to salary_min",
        )

    query = db.query(Job)

    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_pattern),
                Job.company.ilike(search_pattern),
            )
        )
    if category_id is not None:
        query = query.filter(Job.category_id == category_id)
    if location and location.strip():
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))

    # A job matches when its offered range overlaps the requested salary range.
    if salary_min is not None:
        query = query.filter(
            Job.salary_max.is_not(None),
            Job.salary_max >= salary_min,
        )
    if salary_max is not None:
        query = query.filter(
            Job.salary_min.is_not(None),
            Job.salary_min <= salary_max,
        )

    total = query.count()
    order_by = {
        "newest": (Job.created_at.desc(), Job.id.desc()),
        "oldest": (Job.created_at.asc(), Job.id.asc()),
        "salary_asc": (Job.salary_min.asc().nullslast(), Job.id.asc()),
        "salary_desc": (Job.salary_max.desc().nullslast(), Job.id.desc()),
    }
    items = (
        query.options(joinedload(Job.category))
        .order_by(*order_by[sort])
        .offset(skip)
        .limit(limit)
        .all()
    )

    return JobPaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/meta/locations", response_model=list[str])
def get_available_locations(db: Session = Depends(get_db)) -> list[str]:
    rows = (
        db.query(Job.location)
        .filter(Job.location.is_not(None), func.trim(Job.location) != "")
        .group_by(Job.location)
        .order_by(func.lower(Job.location).asc())
        .all()
    )
    return [location for (location,) in rows]


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)) -> Job:
    return get_job_or_404(job_id, db)


@router.put(
    "/{job_id}",
    response_model=JobResponse,
    dependencies=[Depends(require_admin)],
)
def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
) -> Job:
    job = get_job_or_404(job_id, db)
    update_data = job_data.model_dump(exclude_unset=True)

    new_category_id = update_data.get("category_id")
    if new_category_id is not None:
        ensure_category_exists(new_category_id, db)

    salary_min = update_data.get("salary_min", job.salary_min)
    salary_max = update_data.get("salary_max", job.salary_max)
    ensure_valid_salary_range(salary_min, salary_max)

    for field, value in update_data.items():
        setattr(job, field, value)

    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        ) from exc

    return job


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_job(job_id: int, db: Session = Depends(get_db)) -> Response:
    job = get_job_or_404(job_id, db)

    try:
        db.delete(job)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
