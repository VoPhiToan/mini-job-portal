from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.security import JWT_ALGORITHM, JWT_SECRET_KEY
from app.database import get_db
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception()
        user_id = int(subject)
    except (JWTError, TypeError, ValueError) as exc:
        raise credentials_exception() from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception()
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_candidate(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate access required",
        )
    return current_user
