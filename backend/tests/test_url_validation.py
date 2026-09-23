import pytest
from fastapi import HTTPException
from app.utils.security import validate_and_sanitize_url


def test_valid_urls():
    assert validate_and_sanitize_url("https://example.com") == "https://example.com"
    assert validate_and_sanitize_url("http://github.com/uiproof") == "http://github.com/uiproof"


def test_invalid_scheme_rejection():
    with pytest.raises(HTTPException) as exc1:
        validate_and_sanitize_url("file:///etc/passwd")
    assert exc1.value.status_code == 400

    with pytest.raises(HTTPException) as exc2:
        validate_and_sanitize_url("ftp://ftp.example.com")
    assert exc2.value.status_code == 400


def test_ssrf_localhost_rejection():
    with pytest.raises(HTTPException) as exc1:
        validate_and_sanitize_url("http://localhost:8000")
    assert exc1.value.status_code == 400

    with pytest.raises(HTTPException) as exc2:
        validate_and_sanitize_url("http://127.0.0.1:3000")
    assert exc2.value.status_code == 400

    with pytest.raises(HTTPException) as exc3:
        validate_and_sanitize_url("http://10.0.0.1")
    assert exc3.value.status_code == 400

    with pytest.raises(HTTPException) as exc4:
        validate_and_sanitize_url("http://192.168.1.1")
    assert exc4.value.status_code == 400


def test_localhost_override_for_tests():
    # allow_localhost=True should allow local URLs during testing
    assert validate_and_sanitize_url("http://localhost:8000", allow_localhost=True) == "http://localhost:8000"
    assert validate_and_sanitize_url("http://127.0.0.1:8000", allow_localhost=True) == "http://127.0.0.1:8000"
