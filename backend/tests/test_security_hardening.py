import pytest
import time
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.utils.security import (
    validate_and_sanitize_url,
    is_ip_prohibited,
    resolve_host_ips,
)
from app.services.rate_limiter import InMemoryRateLimiter, extract_client_ip
from app.services.auth import create_access_token, verify_password, hash_password, decode_access_token, InvalidTokenError

client = TestClient(app)


# ============================================================================
# 1. RATE LIMITING TESTS
# ============================================================================

def test_rate_limiter_threshold_and_429_header():
    limiter = InMemoryRateLimiter(requests_per_minute=3, cleanup_interval_sec=60)
    key = "test_user_ip"

    for _ in range(3):
        is_limited, retry_after = limiter.is_rate_limited(key)
        assert is_limited is False
        assert retry_after == 0

    is_limited, retry_after = limiter.is_rate_limited(key)
    assert is_limited is True
    assert retry_after > 0


def test_auth_endpoint_rate_limiting():
    headers = {"Content-Type": "application/json"}
    responses = []
    for i in range(12):
        res = client.post(
            "/api/v1/auth/register",
            json={"email": f"ratelimit_user_{i}@example.com", "password": "Password123!"},
            headers=headers
        )
        responses.append(res)

    statuses = [r.status_code for r in responses]
    assert 429 in statuses
    
    res_429 = next(r for r in responses if r.status_code == 429)
    assert "retry-after" in res_429.headers
    assert res_429.json()["detail"] == "Too many requests. Please slow down and try again later."


def test_proxy_ip_extraction_rightmost_header():
    class DummyClient:
        host = "127.0.0.1"

    class DummyRequest:
        headers = {"x-forwarded-for": "1.2.3.4, 203.0.113.195"}
        client = DummyClient()

    ip = extract_client_ip(DummyRequest())
    assert ip == "203.0.113.195"


# ============================================================================
# 2. SSRF & IP DESTINATION VALIDATION TESTS
# ============================================================================

@pytest.mark.parametrize("private_ip", [
    "127.0.0.1",
    "127.0.0.255",
    "10.0.0.1",
    "10.255.255.255",
    "172.16.0.1",
    "172.31.255.255",
    "192.168.0.1",
    "192.168.255.255",
    "169.254.169.254",        # AWS/GCP Metadata
    "169.254.0.1",
    "0.0.0.0",
    "::1",
    "::",
    "fe80::1",                # Link-local IPv6
    "fc00::1",                # Unique Local IPv6 (ULA)
    "100.64.0.1",             # Carrier-Grade NAT (CGNAT)
    "192.0.2.1",              # Documentation network
    "198.51.100.1",           # Documentation network
    "203.0.113.1",            # Documentation network
    "2001:db8::1",            # IPv6 Documentation
    "::ffff:127.0.0.1",       # IPv4-mapped IPv6 loopback
    "::ffff:169.254.169.254", # IPv4-mapped IPv6 metadata
    "::ffff:10.0.0.1",        # IPv4-mapped IPv6 private
    "::ffff:100.64.0.1",      # IPv4-mapped IPv6 CGNAT
])
def test_is_ip_prohibited_filters_all_restricted_address_classes(private_ip):
    assert is_ip_prohibited(private_ip) is True


def test_is_ip_prohibited_allows_public_ips():
    assert is_ip_prohibited("8.8.8.8") is False
    assert is_ip_prohibited("1.1.1.1") is False
    assert is_ip_prohibited("93.184.216.34") is False


@pytest.mark.parametrize("invalid_url", [
    "http://127.0.0.1/admin",
    "http://localhost/secret",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.1/internal",
    "http://172.16.0.1/internal",
    "http://192.168.1.1/router",
    "http://[::1]/admin",
    "http://[::ffff:127.0.0.1]/test",
    "http://[::ffff:169.254.169.254]/metadata",
    "http://user:password@example.com/login",      # Embedded credentials
    "http://example.com@127.0.0.1/test",           # Userinfo confusion targeting 127.0.0.1
    "http://127.1/admin",                          # Shortened IPv4 loopback
    "http://2130706433/admin",                     # Integer IPv4 loopback
    "http://0x7f000001/admin",                     # Hex IPv4 loopback
    "ftp://example.com/file",                      # Non-HTTP scheme
    "file:///etc/passwd",                          # File scheme
    "gopher://example.com",                        # Gopher scheme
])
def test_validate_and_sanitize_url_rejects_ssrf_and_invalid_urls(invalid_url):
    with pytest.raises(HTTPException) as exc_info:
        validate_and_sanitize_url(invalid_url, mode="remote", is_production=False)
    assert exc_info.value.status_code == 400


def test_validate_and_sanitize_url_allows_valid_public_urls():
    valid_url = "https://example.com/about?test=1"
    res = validate_and_sanitize_url(valid_url, mode="remote", is_production=False)
    assert res == valid_url

    # Mixed-case scheme support
    res_mixed = validate_and_sanitize_url("hTtPs://example.com/path", mode="remote", is_production=False)
    assert res_mixed == "hTtPs://example.com/path"


def test_validate_and_sanitize_url_rejects_mixed_public_and_private_dns_answers(monkeypatch):
    # Mock DNS resolution to return a mix of public and private IPs for a single domain
    def mock_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return [
            (2, 1, 6, '', ('93.184.216.34', 80)),
            (2, 1, 6, '', ('10.0.0.1', 80)),
        ]

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)
    
    with pytest.raises(HTTPException) as exc_info:
        validate_and_sanitize_url("http://mixed-dns-target.com", mode="remote", is_production=False)
    assert exc_info.value.status_code == 400
    assert "prohibited" in exc_info.value.detail.lower() or "restricted" in exc_info.value.detail.lower()


# ============================================================================
# 3. URL VALIDATION & HOSTILE STRING TESTS (XSS REGRESSION)
# ============================================================================

def test_hostile_url_string_validation():
    hostile_url = "https://example.com/search?q=<script>alert('xss')</script>"
    res = validate_and_sanitize_url(hostile_url, mode="remote", is_production=False)
    assert res == hostile_url


# ============================================================================
# 4. JWT & AUTHENTICATION CONFIGURATION TESTS
# ============================================================================

def test_jwt_token_validation_expired_and_malformed():
    from datetime import timedelta

    with pytest.raises(InvalidTokenError):
        decode_access_token("invalid.token.structure")

    expired_token = create_access_token(
        user_id="usr_test",
        email="test@example.com",
        expires_delta=timedelta(minutes=-10)
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(expired_token)


def test_password_hashing_verification():
    raw_pwd = "SecurePassword123!"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


# ============================================================================
# 5. SECURITY HEADERS & CORS TESTS
# ============================================================================

def test_api_security_headers_present():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in res.headers.get("permissions-policy", "")


def test_cors_preflight_and_origin_headers():
    # OPTIONS preflight check
    res = client.options(
        "/api/v1/projects",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"}
    )
    assert res.status_code in (200, 204)
