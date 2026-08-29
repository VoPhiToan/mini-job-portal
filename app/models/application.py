from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_id",
            name="uq_application_user_job",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
