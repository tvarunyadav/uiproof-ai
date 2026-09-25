import logging
import bcrypt

logger = logging.getLogger("uiproof.security")


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt algorithm.
    Never stores or returns plaintext passwords.
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string.")

    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.
    Returns True if matches, False otherwise.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        plain_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as err:
        logger.warning("Password verification failed unexpectedly: %s", type(err).__name__)
        return False
