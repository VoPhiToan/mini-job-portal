import argparse

from sqlalchemy import and_, or_

from app.database import SessionLocal
from app.models.application import Application
from app.models.category import Category
from app.models.job import Job
from app.models.user import User


VERIFICATION_CATEGORY_NAMES = {
    "Phase 8 Verification",
    "Phase 8.1 Verification",
}
VERIFICATION_JOB_TITLES = {
    "Phase 8 Verification Job",
    "Phase 8 Verification Withdrawal Job",
    "Phase 8.1 Verification Job",
    "Phase 8.1 Verification Pending Job",
    "Phase 8.1 Verification Accepted Job",
    "Phase 8.1 Verification Rejected Job",
    "Phase 8.1 Verification Empty Job",
}
VERIFICATION_COMPANY = "MiniJob Test Company"
VERIFICATION_USER_NAMES = {
    "Phase 8 Verification Admin",
    "Phase 8 Verification Candidate",
    "Phase 8.1 Verification Admin",
    "Phase 8.1 Verification Candidate",
}


def verification_user_filter():
    return and_(
        User.full_name.in_(VERIFICATION_USER_NAMES),
        or_(
            User.email.like("phase8-admin-%@example.com"),
            User.email.like("phase8-candidate-%@example.com"),
            User.email.like("phase8-1-admin-%@example.com"),
            User.email.like("phase8-1-candidate-%@example.com"),
        ),
    )


def verification_job_filter():
    return and_(
        Job.title.in_(VERIFICATION_JOB_TITLES),
        Job.company == VERIFICATION_COMPANY,
    )


def collect_records(db):
    users = db.query(User).filter(verification_user_filter()).all()
    jobs = db.query(Job).filter(verification_job_filter()).all()
    categories = (
        db.query(Category)
        .filter(Category.name.in_(VERIFICATION_CATEGORY_NAMES))
        .all()
    )
    user_ids = [user.id for user in users]
    job_ids = [job.id for job in jobs]
    application_filters = []
    if user_ids:
        application_filters.append(Application.user_id.in_(user_ids))
    if job_ids:
        application_filters.append(Application.job_id.in_(job_ids))
    applications = (
        db.query(Application).filter(or_(*application_filters)).all()
        if application_filters
        else []
    )
    return users, jobs, categories, applications


def report_records(users, jobs, categories, applications) -> None:
    print(f"Verification users: {len(users)} (IDs: {[user.id for user in users]})")
    print(f"Verification jobs: {len(jobs)} (IDs: {[job.id for job in jobs]})")
    print(
        "Verification categories: "
        f"{len(categories)} (IDs: {[category.id for category in categories]})"
    )
    print(
        "Verification applications: "
        f"{len(applications)} (IDs: {[application.id for application in applications]})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean only explicitly marked Phase 8 verification records."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        users, jobs, categories, applications = collect_records(db)
        report_records(users, jobs, categories, applications)

        if not args.execute:
            print("Dry run only. No records were deleted.")
            return

        for application in applications:
            db.delete(application)
        db.flush()

        for job in jobs:
            db.delete(job)
        db.flush()

        for category in categories:
            has_jobs = db.query(Job.id).filter(Job.category_id == category.id).first()
            if not has_jobs:
                db.delete(category)
        db.flush()

        for user in users:
            db.delete(user)

        db.commit()
        print("Verification cleanup completed successfully.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
