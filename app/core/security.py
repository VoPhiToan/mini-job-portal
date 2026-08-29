import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import jwt
from passlib.context import CryptContext


load_dotenv()


def get_required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not configured in the environment")
    return value


JWT_SECRET_KEY = get_required_setting("JWT_SECRET_KEY")
JWT_ALGORITHM = get_required_setting("JWT_ALGORITHM")

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        get_required_setting("ACCESS_TOKEN_EXPIRE_MINUTES")
    )
except ValueError as exc:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be an integer") from exc

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero")

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    payload = data.copy()
    expires_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["exp"] = expires_at
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
