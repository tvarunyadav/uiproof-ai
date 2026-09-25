from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import UserModel
from app.services.auth.jwt import decode_access_token
from app.services.auth.exceptions import InvalidTokenError, UserNotFoundError


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
