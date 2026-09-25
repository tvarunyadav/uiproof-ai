import pytest
import jwt
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.db.models import UserModel
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
    InvalidTokenError,
    UserNotFoundError,
)


# ==============================================================================
# PASSWORD HASHING TESTS (1-5)
# ==============================================================================

def test_password_hashing_non_plaintext():
    """Test 1: Password hashing produces a non-plaintext value."""
    plain = "MySecretPassword123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert "$2b$" in hashed or "$2a$" in hashed
    assert len(hashed) > 30


def test_password_verification_success():
    """Test 2: Same password verifies successfully."""
    plain = "MySecretPassword123!"
    hashed = hash_password(plain)

    assert verify_password(plain, hashed) is True


def test_password_verification_failure():
    """Test 3: Wrong password fails verification."""
    plain = "MySecretPassword123!"
    hashed = hash_password(plain)

    assert verify_password("WrongPassword456!", hashed) is False


def test_password_hash_persistence(db_session):
    """Test 4: Hash can be verified after persistence/reconstruction in UserModel."""
    plain = "PersistedPass999!"
    hashed = hash_password(plain)

    user = UserModel(
        user_id="usr_persist",
        email="persist@test.com",
        password_hash=hashed,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()

    reconstructed = db_session.query(UserModel).filter_by(user_id="usr_persist").first()
    assert reconstructed is not None
    assert verify_password(plain, reconstructed.password_hash) is True
    assert verify_password("BadPass", reconstructed.password_hash) is False


def test_empty_password_handling():
    """Test 5: Empty/invalid password handling follows a deliberate rule."""
    with pytest.raises(ValueError):
        hash_password("")

    assert verify_password("", "$2b$12$abcdef...") is False
    assert verify_password("plain", "") is False


# ==============================================================================
# JWT TESTS (6-15)
# ==============================================================================

def test_jwt_creation_and_claims():
    """Tests 6, 7, 8, 9: Access token created with sub, email, iat, and exp claims."""
    user_id = "usr_jwt_001"
    email = "jwt@example.com"

    token = create_access_token(user_id=user_id, email=email)
    assert isinstance(token, str)
    assert len(token) > 20

    # Decode without verifying to inspect payload claims directly
    unverified = jwt.decode(token, options={"verify_signature": False})
    assert unverified["sub"] == user_id
    assert unverified["email"] == email
    assert "iat" in unverified
    assert "exp" in unverified
    assert unverified["exp"] > unverified["iat"]


def test_jwt_valid_decode():
    """Test 10: Valid token decodes successfully."""
    token = create_access_token("usr_valid", "valid@example.com")
    decoded = decode_access_token(token)

    assert decoded["sub"] == "usr_valid"
    assert decoded["email"] == "valid@example.com"


def test_jwt_expired_rejection():
    """Test 11: Expired token is rejected."""
    # Create token expired 10 minutes ago
    expired_token = create_access_token(
        "usr_expired",
        "expired@example.com",
        expires_delta=timedelta(minutes=-10)
    )

    with pytest.raises(InvalidTokenError) as exc_info:
        decode_access_token(expired_token)
    assert "expired" in str(exc_info.value).lower()


def test_jwt_tampered_rejection():
    """Test 12: Tampered token signature is rejected."""
    valid_token = create_access_token("usr_tamper", "tamper@example.com")
    tampered_token = valid_token[:-5] + "XXXXX"

    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered_token)


def test_jwt_malformed_rejection():
    """Test 13: Malformed token string is rejected."""
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-valid-jwt-token-string")


def test_jwt_missing_sub_rejection():
    """Test 14: Token without 'sub' claim is rejected."""
    payload = {
        "email": "nosub@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    invalid_sub_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(InvalidTokenError) as exc_info:
        decode_access_token(invalid_sub_token)
    assert "subject" in str(exc_info.value).lower() or "sub" in str(exc_info.value).lower()


def test_token_referencing_nonexistent_user_rejected(db_session):
    """Test 15: Token referencing nonexistent user is rejected by current user resolver."""
    token = create_access_token("usr_ghost_999", "ghost@example.com")

    with pytest.raises(UserNotFoundError) as exc_info:
        get_current_user(token, db=db_session)
    assert "ghost_999" in str(exc_info.value)


# ==============================================================================
# CURRENT USER TESTS (16-18)
# ==============================================================================

def test_get_current_user_valid(db_session):
    """Test 16: Valid token resolves the correct UserModel."""
    user = UserModel(
        user_id="usr_current_001",
        email="current@test.com",
        password_hash=hash_password("Pass123!"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.user_id, user.email)
    resolved_user = get_current_user(token, db=db_session)

    assert resolved_user is not None
    assert resolved_user.user_id == "usr_current_001"
    assert resolved_user.email == "current@test.com"


def test_get_current_user_invalid_token(db_session):
    """Test 17: Invalid token is rejected when resolving current user."""
    with pytest.raises(InvalidTokenError):
        get_current_user("bad.token.value", db=db_session)


def test_get_current_user_deleted_user(db_session):
    """Test 18: Deleted/nonexistent user token is rejected."""
    user = UserModel(
        user_id="usr_to_delete",
        email="delete@test.com",
        password_hash=hash_password("Pass123!"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.user_id, user.email)

    # Delete user from DB
    db_session.delete(user)
    db_session.commit()

    with pytest.raises(UserNotFoundError):
        get_current_user(token, db=db_session)


# ==============================================================================
# CONFIGURATION TESTS (19-20)
# ==============================================================================

def test_jwt_configuration_loading():
    """Test 19: JWT configuration loads correctly from application settings."""
    assert hasattr(settings, "JWT_SECRET_KEY")
    assert hasattr(settings, "JWT_ALGORITHM")
    assert hasattr(settings, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0


def test_jwt_secret_not_hardcoded():
    """Test 20: Secret is sourced from configuration settings and dynamically customizable."""
    custom_secret = "custom-test-secret-key-32-chars-long!"
    payload = {"sub": "usr_custom", "email": "c@test.com", "exp": datetime.now(timezone.utc) + timedelta(minutes=10)}
    token = jwt.encode(payload, custom_secret, algorithm="HS256")

    # Trying to decode with default settings secret should fail
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_production_environment_jwt_secret_validation():
    """Test 21: Production environment rejects default development placeholder secret."""
    from app.config import Settings, DEV_PLACEHOLDER_JWT_SECRET
    from pydantic import ValidationError

    # In production with placeholder secret, validation must fail
    with pytest.raises(ValidationError) as exc_info:
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY=DEV_PLACEHOLDER_JWT_SECRET)
    assert "JWT_SECRET_KEY must be explicitly configured" in str(exc_info.value)

    # In production with real custom secret, validation succeeds
    prod_settings = Settings(ENVIRONMENT="production", JWT_SECRET_KEY="production-real-secret-key-32chars-long!")
    assert prod_settings.JWT_SECRET_KEY == "production-real-secret-key-32chars-long!"
