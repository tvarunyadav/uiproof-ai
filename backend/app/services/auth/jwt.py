import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from app.config import settings
from app.services.auth.exceptions import InvalidTokenError

logger = logging.getLogger("uiproof.auth.jwt")


def create_access_token(user_id: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT access token containing subject (user_id), email, iat, and exp claims.
    Secrets and algorithm are sourced directly from application Settings.
    """
    if not user_id or not isinstance(user_id, str):
        raise ValueError("user_id must be a non-empty string.")
    if not email or not isinstance(email, str):
        raise ValueError("email must be a non-empty string.")

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a signed JWT access token.
    Enforces signature verification, expiration check, and required claim presence.
    Raises InvalidTokenError for any validation failure without leaking sensitive secrets.
    """
    if not token or not isinstance(token, str):
        raise InvalidTokenError("Token must be a non-empty string.")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        sub = payload.get("sub")
        if not sub or not isinstance(sub, str):
            raise InvalidTokenError("Token payload missing required subject claim ('sub').")

        return payload
    except jwt.ExpiredSignatureError:
        raise InvalidTokenError("Access token has expired.")
    except jwt.PyJWTError as err:
        raise InvalidTokenError(f"Invalid access token signature or format.")
