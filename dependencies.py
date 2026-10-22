"""Reusable request helpers: database session, current user, and role checks."""
from collections.abc import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User
from utils.security import read_token_user_id

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerToken")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
                     db: Session = Depends(get_db)) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in and provide your bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user_id = read_token_user_id(token)
    user = db.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your login token is invalid or expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_manager_or_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in {"project_manager", "admin"}:
        raise HTTPException(status_code=403, detail="A project manager or admin account is required")
    return user
