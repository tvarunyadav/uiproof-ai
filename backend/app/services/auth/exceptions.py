class AuthenticationError(Exception):
    """Base exception for authentication failures."""
    pass


class InvalidTokenError(AuthenticationError):
    """Raised when a JWT access token is invalid, expired, or malformed."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when authentication credentials (email/password) are incorrect."""
    pass


class UserNotFoundError(AuthenticationError):
    """Raised when a user referenced in a token payload does not exist in the database."""
    pass
