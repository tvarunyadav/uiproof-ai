import pytest
from fastapi import HTTPException
from unittest.mock import patch, AsyncMock
from app.utils.security import validate_and_sanitize_url
from app.schemas.audit import CreateAuditRequest, AuditResult, AuditStatus
from app.services.auth import create_access_token, hash_password
from app.db.models import UserModel
from datetime import datetime, timezone


def test_case_a_dev_local_localhost():
    """Case A: Development + local + localhost -> ALLOWED"""
    res = validate_and_sanitize_url("http://localhost:5173", mode="local", is_production=False)
    assert res == "http://localhost:5173"


def test_case_b_dev_local_127_0_0_1():
    """Case B: Development + local + 127.0.0.1 -> ALLOWED"""
    res = validate_and_sanitize_url("http://127.0.0.1:3000", mode="local", is_production=False)
    assert res == "http://127.0.0.1:3000"


def test_case_c_dev_local_0_0_0_0():
    """Case C: Development + local + 0.0.0.0 -> REJECTED"""
    with pytest.raises(HTTPException) as exc:
        validate_and_sanitize_url("http://0.0.0.0:8000", mode="local", is_production=False)
    assert exc.value.status_code == 400
    assert "0.0.0.0" in str(exc.value.detail)


def test_case_d_dev_local_public_url():
    """Case D: Development + local + public URL -> REJECTED"""
    with pytest.raises(HTTPException) as exc:
        validate_and_sanitize_url("https://example.com", mode="local", is_production=False)
    assert exc.value.status_code == 400


def test_case_e_dev_remote_public_url():
    """Case E: Development + remote + public URL -> ALLOWED"""
    res = validate_and_sanitize_url("https://example.com", mode="remote", is_production=False)
    assert res == "https://example.com"


def test_case_f_dev_remote_localhost():
    """Case F: Development + remote + localhost -> REJECTED"""
    with pytest.raises(HTTPException) as exc:
        validate_and_sanitize_url("http://localhost:5173", mode="remote", is_production=False)
    assert exc.value.status_code == 400


def test_case_g_dev_remote_private_ip():
    """Case G: Development + remote + private IP -> REJECTED"""
    with pytest.raises(HTTPException) as exc:
        validate_and_sanitize_url("http://192.168.1.1:8000", mode="remote", is_production=False)
    assert exc.value.status_code == 400


def test_case_h_prod_local_localhost():
    """Case H: Production + local + localhost -> REJECTED"""
    with pytest.raises(HTTPException) as exc:
        validate_and_sanitize_url("http://localhost:5173", mode="local", is_production=True)
    assert exc.value.status_code == 400


def test_case_i_prod_remote_localhost():
    """Case I: Production + remote + localhost -> REJECTED"""
    with pytest.raises(HTTPException) as exc:
        validate_and_sanitize_url("http://localhost:5173", mode="remote", is_production=True)
    assert exc.value.status_code == 400


def test_case_j_prod_remote_public_url():
    """Case J: Production + remote + public URL -> ALLOWED"""
    res = validate_and_sanitize_url("https://example.com", mode="remote", is_production=True)
    assert res == "https://example.com"


def test_case_k_file_protocol():
    """Case K: file:// -> REJECTED"""
    with pytest.raises(HTTPException) as exc:
        validate_and_sanitize_url("file:///etc/passwd", mode="local", is_production=False)
    assert exc.value.status_code == 400


def test_case_l_invalid_mode():
    """Case L: invalid mode -> HTTP 400"""
    with pytest.raises(HTTPException) as exc:
        validate_and_sanitize_url("https://example.com", mode="invalid_mode", is_production=False)
    assert exc.value.status_code == 400


def test_case_m_omitted_mode():
    """Case M: omitted mode -> defaults to remote (allows public, rejects localhost)"""
    res = validate_and_sanitize_url("https://example.com", is_production=False)
    assert res == "https://example.com"
    with pytest.raises(HTTPException) as exc:
        validate_and_sanitize_url("http://localhost:5173", is_production=False)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_audit_endpoint_local_mode_success(async_client, db_session):
    """Integration Test: Create audit with mode='local' succeeds in dev."""
    user = UserModel(
        user_id="usr_local_test",
        email="local@test.com",
        password_hash=hash_password("Password123!"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.user_id, user.email)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "url": "http://localhost:5173",
        "mode": "local",
        "viewports": ["desktop"]
    }

    # Mock Playwright execution to prevent real browser launch during unit tests
    with patch("app.services.audit.audit_engine.browser_runner.collect_evidence", new_callable=AsyncMock) as mock_collect:
        from app.schemas.evidence import BrowserEvidence, ViewportAuditResult, BrowserViewport, PageMetadata, ResponsiveMetrics
        mock_collect.return_value = BrowserEvidence(
            url="http://localhost:5173",
            timestamp=datetime.now(timezone.utc).isoformat(),
            desktop=ViewportAuditResult(
                viewport=BrowserViewport(name="Desktop", width=1440, height=900, device_scale_factor=1.0),
                page=PageMetadata(initial_url="http://localhost:5173", final_url="http://localhost:5173", title="Local App", page_load_success=True),
                console_errors=[],
                network_failures=[],
                responsive=ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0)
            ),
            viewports_tested=[],
            screenshot_paths=[],
            console_errors=[],
            network_failures=[],
            layout_issues=[],
            accessibility_issues=[]
        )

        res = await async_client.post("/api/v1/audits", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["url"] == "http://localhost:5173"
        assert data["mode"] == "local"
        assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_create_audit_endpoint_backward_compatibility_omitted_mode(async_client, db_session):
    """TEST 12: Request without mode defaults to 'remote' and succeeds for public HTTPS."""
    user = UserModel(
        user_id="usr_compat_test",
        email="compat@test.com",
        password_hash=hash_password("Password123!"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.user_id, user.email)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "url": "https://example.com"
        # mode omitted
    }

    with patch("app.services.audit.audit_engine.browser_runner.collect_evidence", new_callable=AsyncMock) as mock_collect:
        from app.schemas.evidence import BrowserEvidence, ViewportAuditResult, BrowserViewport, PageMetadata, ResponsiveMetrics
        mock_collect.return_value = BrowserEvidence(
            url="https://example.com",
            timestamp=datetime.now(timezone.utc).isoformat(),
            desktop=ViewportAuditResult(
                viewport=BrowserViewport(name="Desktop", width=1440, height=900, device_scale_factor=1.0),
                page=PageMetadata(initial_url="https://example.com", final_url="https://example.com", title="Example", page_load_success=True),
                console_errors=[],
                network_failures=[],
                responsive=ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0)
            ),
            viewports_tested=[],
            screenshot_paths=[],
            console_errors=[],
            network_failures=[],
            layout_issues=[],
            accessibility_issues=[]
        )

        res = await async_client.post("/api/v1/audits", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["mode"] == "remote"
