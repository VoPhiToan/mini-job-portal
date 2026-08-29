from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies.auth import require_admin, require_candidate
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.schemas.application import (
    ApplicationAdminResponse,
    ApplicationCandidateSummary,
    ApplicationResponse,
    ApplicationStatusUpdate,
    ApplicationWithJobResponse,
)


router = APIRouter(tags=["Applications"])


def application_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Application not found",
    )


def to_admin_response(application: Application) -> ApplicationAdminResponse:
    return ApplicationAdminResponse(
        id=application.id,
        status=application.status,
        created_at=application.created_at,
        candidate=ApplicationCandidateSummary.model_validate(application.user),
        job=application.job,
    )


@router.post(
    "/jobs/{job_id}/apply",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_to_job(
    job_id: int,
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> Application:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    existing_application = (
        db.query(Application)
        .filter(
            Application.user_id == current_user.id,
            Application.job_id == job_id,
        )
        .first()
    )
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already applied to this job",
        )

    application = Application(
        user_id=current_user.id,
        job_id=job_id,
        status="pending",
    )
    try:
        db.add(application)
        db.commit()
        db.refresh(application)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already applied to this job",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        ) from exc

    return application


@router.get(
    "/applications/me",
    response_model=list[ApplicationWithJobResponse],
)
def get_my_applications(
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> list[Application]:
    return (
        db.query(Application)
        .options(joinedload(Application.job))
        .filter(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc(), Application.id.desc())
        .all()
    )


@router.get(
    "/applications/me/{application_id}",
    response_model=ApplicationWithJobResponse,
)
def get_my_application(
    application_id: int,
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> Application:
    application = (
        db.query(Application)
        .options(joinedload(Application.job))
        .filter(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
        .first()
    )
    if not application:
        raise application_not_found()
    return application


@router.delete(
    "/applications/me/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def withdraw_application(
    application_id: int,
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> Response:
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
        .first()
    )
    if not application:
        raise application_not_found()
    if application.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending applications can be withdrawn",
        )

    try:
        db.delete(application)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/admin/applications",
    response_model=list[ApplicationAdminResponse],
)
def get_all_applications(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[ApplicationAdminResponse]:
    applications = (
        db.query(Application)
        .options(joinedload(Application.user), joinedload(Application.job))
        .order_by(Application.created_at.desc(), Application.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [to_admin_response(application) for application in applications]


@router.get(
    "/admin/applications/{application_id}",
    response_model=ApplicationAdminResponse,
)
def get_application_for_admin(
    application_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApplicationAdminResponse:
    application = (
        db.query(Application)
        .options(joinedload(Application.user), joinedload(Application.job))
        .filter(Application.id == application_id)
        .first()
    )
    if not application:
        raise application_not_found()
    return to_admin_response(application)


@router.patch(
    "/admin/applications/{application_id}/status",
    response_model=ApplicationAdminResponse,
)
def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApplicationAdminResponse:
    application = (
        db.query(Application)
        .options(joinedload(Application.user), joinedload(Application.job))
        .filter(Application.id == application_id)
        .first()
    )
    if not application:
        raise application_not_found()

    application.status = status_data.status
    try:
        db.add(application)
        db.commit()
        db.refresh(application)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        ) from exc

    return to_admin_response(application)
