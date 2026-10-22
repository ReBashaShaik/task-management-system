"""Register users and verify logins."""
from sqlalchemy.orm import Session

from models import User
from schemas import UserCreate
from utils.security import create_access_token, hash_password, verify_password
from services.errors import AuthenticationError, ConflictError


def register_user(data: UserCreate, db: Session) -> User:
    """Create a member or project manager with a hashed password."""
    if db.query(User).filter(User.email == data.email).first():
        raise ConflictError("An account with this email already exists")

    user = User(name=data.name, email=data.email,
                hashed_password=hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(email: str, password: str, db: Session) -> dict[str, str]:
    """Check a password and return a signed login token."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password) or not user.is_active:
        raise AuthenticationError("Email or password is incorrect")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}
