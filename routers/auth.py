"""HTTP endpoints for registration and login."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Form
from pydantic import EmailStr
from sqlalchemy.orm import Session

from dependencies import get_db
from schemas import UserCreate, UserOut, require_gmail_address
from services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Create a member or project manager account."""
    return auth_service.register_user(data, db)


@router.post("/login")
def login(email: EmailStr = Form(...), password: str = Form(..., min_length=8, max_length=72),
          db: Session = Depends(get_db)):
    """Check the email/password form and return a JWT access token."""
    try:
        require_gmail_address(str(email))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return auth_service.login_user(str(email), password, db)
