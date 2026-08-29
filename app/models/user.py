from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="candidate")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    applications = relationship(
        "Application",
        back_populates="user",
        cascade="all, delete-orphan",
    )
