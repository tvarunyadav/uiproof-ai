import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.models import UserModel
from app.services.auth import create_access_token, hash_password
from app.config import settings
from app.db.session import get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_db_dependency(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()



# ==============================================================================
# REGISTRATION TESTS (1-7)
# ==============================================================================

def test_register_success(db_session):
    """
    Tests 1, 2, 3, 4: Successful registration returns 201, persists user with hashed password,
    and does NOT expose password or password_hash.
    """
    payload = {
        "email": "newuser@example.com",
        "password": "SecurePassword123!"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert "user_id" in data
    assert data["user_id"].startswith("usr_")
    assert data["email"] == "newuser@example.com"
    assert "password" not in data
    assert "password_hash" not in data

    # Verify database persistence
    db_user = db_session.query(UserModel).filter_by(email="newuser@example.com").first()
    assert db_user is not None
    assert db_user.password_hash != "SecurePassword123!"
    assert "$2b$" in db_user.password_hash


def test_register_duplicate_email(db_session):
    """
    Test 5: Registering with an existing email returns 409 Conflict.
    """
    existing_user = UserModel(
        user_id="usr_dup",
        email="duplicate@example.com",
        password_hash=hash_password("Pass123!"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(existing_user)
    db_session.commit()

    res = client.post("/api/v1/auth/register", json={"email": "duplicate@example.com", "password": "NewPassword123!"})
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"].lower()


def test_register_email_normalization():
    """
    Test 6: Email input is normalized (lowercased & trimmed) consistently.
    """
    res = client.post("/api/v1/auth/register", json={"email": "  CaseUser@Example.COM  ", "password": "SecurePassword123!"})
    assert res.status_code == 201
    assert res.json()["email"] == "caseuser@example.com"


def test_register_invalid_input():
    """
    Test 7: Invalid registration input (invalid email, short password) returns 422.
    """
    # Invalid email format
    res_bad_email = client.post("/api/v1/auth/register", json={"email": "not-an-email", "password": "SecurePassword123!"})
    assert res_bad_email.status_code == 422

    # Password too short (< 8 chars)
    res_short_pwd = client.post("/api/v1/auth/register", json={"email": "user@example.com", "password": "short"})
    assert res_short_pwd.status_code == 422


# ==============================================================================
# LOGIN TESTS (8-14)
# ==============================================================================

def test_login_success(db_session):
    """
    Tests 8, 9, 10, 14: Successful login returns 200 with access_token (bearer type) and no password_hash.
    """
    user = UserModel(
        user_id="usr_login",
        email="loginuser@example.com",
        password_hash=hash_password("CorrectPassword123!"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()

    res = client.post("/api/v1/auth/login", json={"email": "loginuser@example.com", "password": "CorrectPassword123!"})
    assert res.status_code == 200
    data = res.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "password" not in data
    assert "password_hash" not in data


def test_login_wrong_password_or_unknown_email(db_session):
    """
    Tests 11, 12, 13: Wrong password and unknown email return identical generic 401 response.
    """
    user = UserModel(
        user_id="usr_login_wrong",
        email="known@example.com",
        password_hash=hash_password("RealPassword123!"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()

    # Wrong password for existing email
    res_wrong_pwd = client.post("/api/v1/auth/login", json={"email": "known@example.com", "password": "WrongPassword!"})
    assert res_wrong_pwd.status_code == 401
    detail_wrong_pwd = res_wrong_pwd.json()["detail"]

    # Unknown email
    res_unknown_email = client.post("/api/v1/auth/login", json={"email": "unknown@example.com", "password": "RealPassword123!"})
    assert res_unknown_email.status_code == 401
    detail_unknown_email = res_unknown_email.json()["detail"]

    # Verify identical failure details to prevent user enumeration
    assert detail_wrong_pwd == "Invalid email or password."
    assert detail_unknown_email == "Invalid email or password."


# ==============================================================================
# /AUTH/ME TESTS (15-22)
# ==============================================================================

def test_get_me_success(db_session):
    """
    Tests 15, 16, 17: Valid Bearer token in Authorization header returns current user profile without password_hash.
    """
    user = UserModel(
        user_id="usr_me_001",
        email="me@example.com",
        password_hash=hash_password("Pass123!"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.user_id, user.email)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["user_id"] == "usr_me_001"
    assert data["email"] == "me@example.com"
    assert "password" not in data
    assert "password_hash" not in data


def test_get_me_missing_header():
    """
    Test 18: Missing Authorization header returns 401.
    """
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_get_me_invalid_token():
    """
    Test 19: Invalid token string returns 401.
    """
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.string"})
    assert res.status_code == 401


def test_get_me_expired_token():
    """
    Test 20: Expired JWT access token returns 401.
    """
    expired_token = create_access_token("usr_expired", "expired@example.com", expires_delta=timedelta(minutes=-5))
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401


def test_get_me_tampered_token():
    """
    Test 21: Signature-tampered token returns 401.
    """
    token = create_access_token("usr_tamper", "tamper@example.com")
    tampered_token = token[:-4] + "FAIL"
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res.status_code == 401


def test_get_me_nonexistent_user(db_session):
    """
    Test 22: Token referencing a deleted/nonexistent user returns 401.
    """
    token = create_access_token("usr_ghost_id", "ghost@example.com")
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


# ==============================================================================
# LOGOUT TESTS (23-24)
# ==============================================================================

def test_logout_success():
    """
    Tests 23, 24: Stateless logout endpoint returns 200 notification without requiring token blacklist/session table.
    """
    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert "Logged out successfully" in res.json()["message"]


# ==============================================================================
# SECURITY & COMPATIBILITY TESTS (25-28)
# ==============================================================================

def test_no_secrets_or_hashes_exposed_in_auth_api(db_session):
    """
    Tests 25, 26, 27, 28: Verify JWT secret, password, and password_hash are never present in responses.
    """
    reg_res = client.post("/api/v1/auth/register", json={"email": "sec@example.com", "password": "SecretPassword123!"})
    reg_text = reg_res.text
    assert settings.JWT_SECRET_KEY not in reg_text
    assert "SecretPassword123!" not in reg_text
    assert "password_hash" not in reg_text

    login_res = client.post("/api/v1/auth/login", json={"email": "sec@example.com", "password": "SecretPassword123!"})
    login_text = login_res.text
    assert settings.JWT_SECRET_KEY not in login_text
    assert "SecretPassword123!" not in login_text
    assert "password_hash" not in login_text
