import getpass
import os

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate


def read_value(environment_name: str, prompt: str, secret: bool = False) -> str:
    value = os.getenv(environment_name)
    if value:
        return value
    return getpass.getpass(prompt) if secret else input(prompt).strip()


def create_admin() -> None:
    try:
        admin_data = UserCreate(
            full_name=read_value("ADMIN_FULL_NAME", "Admin full name: "),
            email=read_value("ADMIN_EMAIL", "Admin email: "),
            password=read_value("ADMIN_PASSWORD", "Admin password: ", secret=True),
        )
    except ValidationError as exc:
        print("Invalid admin information.")
        raise SystemExit(1) from exc

    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.email == admin_data.email).first()
        if existing_user:
            print("A user with this email already exists.")
            return

        admin = User(
            full_name=admin_data.full_name,
            email=admin_data.email,
            password_hash=hash_password(admin_data.password),
            role="admin",
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully.")
    except IntegrityError:
        db.rollback()
        print("A user with this email already exists.")
    except SQLAlchemyError as exc:
        db.rollback()
        print("Could not create admin user due to a database error.")
        raise SystemExit(1) from exc
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
