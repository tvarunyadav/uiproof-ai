from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.db.models import UserModel
from app.services.auth.jwt import decode_access_token
from app.services.auth.exceptions import InvalidTokenError, UserNotFoundError

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(token: str, db: Optional[Session] = None) -> UserModel:
    """
    Decodes and validates a Bearer JWT access token, extracts user_id from 'sub' claim,
    and resolves the corresponding UserModel from the database.
    Raises InvalidTokenError or UserNotFoundError if token or user resolution fails.
    """
    payload = decode_access_token(token)
    user_id = payload["sub"]

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        user = db.query(UserModel).filter_by(user_id=user_id).first()
        if not user:
            raise UserNotFoundError(f"User with ID '{user_id}' referenced in token was not found.")
        return user
    finally:
        if close_db:
            db.close()


async def get_current_user_dep(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    FastAPI dependency helper to resolve current authenticated user from HTTP Bearer Authorization header.
    Raises HTTP 401 Unauthorized if missing, expired, malformed, or invalid token.
    """
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


