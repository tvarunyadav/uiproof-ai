import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.db.models import UserModel
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
    LogoutResponse,
)
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    InvalidTokenError,
    UserNotFoundError,
)

logger = logging.getLogger("uiproof.api.auth")
router = APIRouter()

# HTTP Bearer authentication scheme for OpenAPI / Swagger UI integration
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user_dep(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """Dependency helper to resolve current user from HTTP Bearer Authorization header."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = credentials.credentials
    try:
        return get_current_user(token, db=db)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: Token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: User no longer exists.",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account with email and password.
    Enforces email uniqueness, hashes password, and returns public user profile.
    """
    email_clean = request.email.strip().lower()

    existing = db.query(UserModel).filter_by(email=email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists."
        )

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    hashed_pwd = hash_password(request.password)

    new_user = UserModel(
        user_id=user_id,
        email=email_clean,
        password_hash=hashed_pwd,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists."
        )

    return new_user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK, tags=["Authentication"])
async def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user credentials and return a signed JWT access token.
    Uses identical HTTP 401 error response for unknown email vs wrong password to prevent user enumeration.
    """
    email_clean = request.email.strip().lower()

    user = db.query(UserModel).filter_by(email=email_clean).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(user_id=user.user_id, email=user.email)
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK, tags=["Authentication"])
async def get_current_user_profile(current_user: UserModel = Depends(get_current_user_dep)):
    """
    Retrieve authenticated user profile based on Bearer JWT token.
    """
    return current_user


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK, tags=["Authentication"])
async def logout_user():
    """
    Stateless JWT logout endpoint.
    Instructs client applications to discard their stored access token.
    """
    return LogoutResponse(message="Logged out successfully.")
