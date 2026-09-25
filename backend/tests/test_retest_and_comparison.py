import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.services.audit import audit_engine
from app.schemas.audit import CreateAuditRequest, AuditResult, AuditStatus, AuditSummaryStats
from app.schemas.evidence import BrowserEvidence, PageMetadata, ViewportAuditResult, BrowserViewport
from app.schemas.issue import generate_deterministic_issue_id, Issue, IssueCategory, IssueSeverity

client = TestClient(app)


def test_console_issue_id_normalization():
    # Console errors with different timestamps or addresses should produce identical deterministic IDs
    log1 = "Uncaught TypeError: Cannot read property 'id' of null at 2026-09-24T20:15:00.123Z (0x7fa890)"
    log2 = "Uncaught TypeError: Cannot read property 'id' of null at 2026-09-24T20:45:30.999Z (0x1234ab)"

    id1 = generate_deterministic_issue_id("CONSOLE-ERROR", "Desktop", log1)
    id2 = generate_deterministic_issue_id("CONSOLE-ERROR", "Desktop", log2)

    assert id1 == id2, "Console error IDs must match despite dynamic timestamps or memory addresses"


@pytest.mark.asyncio
async def test_retest_endpoint_not_found(db_session):
    from app.db.session import get_db
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db

    try:
        from app.db.models import UserModel
        from app.services.auth import create_access_token, hash_password
        user = UserModel(user_id="usr_rc_001", email="rc1@example.com", password_hash=hash_password("Pass123!"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()
        token = create_access_token(user.user_id, user.email)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/audits/non-existent-uuid", headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_retest_endpoint_success_and_comparison(db_session):
    from app.db.session import get_db
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db

    try:
        from app.db.models import UserModel
        from app.services.auth import create_access_token, hash_password
        user = UserModel(user_id="usr_rc_002", email="rc2@example.com", password_hash=hash_password("Pass123!"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()
        token = create_access_token(user.user_id, user.email)
        headers = {"Authorization": f"Bearer {token}"}

        vp = BrowserViewport(name="Desktop", width=1440, height=900, device_scale_factor=1.0)
        
        issue_meta = Issue(
            issue_id="UI-MISSING-META-DESKTOP",
            category=IssueCategory.SEO,
            severity=IssueSeverity.LOW,
            title="Missing Meta Description (Desktop)",
            description="Missing meta description tag.",
            viewport="Desktop"
        )

        issue_fixed = Issue(
            issue_id="UI-OVERFLOW-DESKTOP",
            category=IssueCategory.RESPONSIVE,
            severity=IssueSeverity.MEDIUM,
            title="Desktop Horizontal Overflow",
            description="Overflow detected.",
            viewport="Desktop"
        )

        baseline_result = AuditResult(
            audit_id="baseline-123",
            target_url="https://testsite.example.com",
            url="https://testsite.example.com",
            status=AuditStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            desktop=ViewportAuditResult(
                viewport=vp,
                page=PageMetadata(initial_url="https://testsite.example.com", final_url="https://testsite.example.com", title="Test", page_load_success=True),
                console_errors=[],
                network_failures=[],
                responsive={"viewport_width": 1440, "viewport_height": 900, "document_scroll_width": 1440, "document_client_width": 1440, "horizontal_overflow": 0}
            ),
            issues=[issue_meta, issue_fixed],
            findings=[issue_meta, issue_fixed],
            stats=AuditSummaryStats(total_issues=2)
        )

        audit_engine._save_audit_to_db(baseline_result, db=db_session)

        # Mock browser evidence collection for retest run
        retest_issue_new = Issue(
            issue_id="UI-CONSOLE-ERROR-DESKTOP-112233",
            category=IssueCategory.CONSOLE_ERROR,
            severity=IssueSeverity.HIGH,
            title="New Console Error",
            description="New console error.",
            viewport="Desktop"
        )

        mock_retest_evidence = BrowserEvidence(
            url="https://testsite.example.com",
            timestamp=datetime.now(timezone.utc),
            desktop=baseline_result.desktop,
            viewports_tested=[vp]
        )

        with patch.object(audit_engine.browser_runner, "collect_evidence", new_callable=AsyncMock) as mock_collect, \
             patch("app.services.audit.create_deterministic_findings", return_value=[issue_meta, retest_issue_new]):

            mock_collect.return_value = mock_retest_evidence

            response = client.post("/api/v1/audits/baseline-123/retest", headers=headers)

            assert response.status_code == 201
            data = response.json()
            assert "retest_audit" in data
            assert "comparison" in data

            retest_audit = data["retest_audit"]
            comp = data["comparison"]

            # Retest must preserve baseline URL
            assert retest_audit["target_url"] == "https://testsite.example.com"
            assert comp["baseline_audit_id"] == "baseline-123"

            # Fixed issue: issue_fixed was in baseline, not in retest
            fixed_ids = [i["issue_id"] for i in comp["fixed_issues"]]
            assert "UI-OVERFLOW-DESKTOP" in fixed_ids

            # Remaining issue: issue_meta was in both
            remaining_ids = [i["issue_id"] for i in comp["remaining_issues"]]
            assert "UI-MISSING-META-DESKTOP" in remaining_ids

            # New issue: retest_issue_new was in retest, not in baseline
            new_ids = [i["issue_id"] for i in comp["new_issues"]]
            assert "UI-CONSOLE-ERROR-DESKTOP-112233" in new_ids
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_comparison_endpoint(db_session):
    from app.db.session import get_db
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db

    try:
        from app.db.models import UserModel
        from app.services.auth import create_access_token, hash_password
        user = UserModel(user_id="usr_rc_003", email="rc3@example.com", password_hash=hash_password("Pass123!"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()
        token = create_access_token(user.user_id, user.email)
        headers = {"Authorization": f"Bearer {token}"}

        # Test GET /api/v1/audits/{audit_id}/compare/{retest_id}
        res = client.get("/api/v1/audits/baseline-123/compare/non-existent", headers=headers)
        assert res.status_code == 404
    finally:
        app.dependency_overrides.clear()

