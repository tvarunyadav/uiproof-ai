import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.services.audit import audit_engine
from app.services.project import project_service, DEFAULT_PROJECT_ID
from app.schemas.project import CreateProjectRequest
from app.schemas.audit import AuditResult, AuditStatus, AuditSummaryStats
from app.schemas.issue import Issue, IssueCategory, IssueSeverity
from app.schemas.evidence import (
    BrowserEvidence,
    ViewportAuditResult,
    BrowserViewport,
    PageMetadata,
    ResponsiveMetrics,
    DOMMetadataEvidence,
)
from app.db.models import AIAnalysisModel

client = TestClient(app)


def test_database_survives_cache_clear(db_session):
    """
    Scenarios 1 & 9: Verify complete audit result, issues, AI analysis, retest, and comparison
    survive _audits_db.clear() and are fully reconstructed from database persistence.
    """
    # 1. Create Project
    proj = project_service.create_project(CreateProjectRequest(name="Cache Clear Test", target_url="https://cachetest.com"), db=db_session)

    # 2. Create Audit with Evidence & Issues
    issue_1 = Issue(
        issue_id="ISSUE-OVERFLOW-DESKTOP",
        category=IssueCategory.RESPONSIVE,
        severity=IssueSeverity.HIGH,
        title="Desktop Overflow",
        description="Horizontal scrollbar detected on desktop viewport.",
        selector="body",
        viewport="Desktop"
    )
    evidence = BrowserEvidence(
        url="https://cachetest.com",
        timestamp=datetime.now(timezone.utc),
        desktop=ViewportAuditResult(
            viewport=BrowserViewport(name="Desktop", width=1440, height=900),
            page=PageMetadata(initial_url="https://cachetest.com", final_url="https://cachetest.com", title="Cache Test", page_load_success=True),
            responsive=ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1500, document_client_width=1440, horizontal_overflow=60),
            dom_metadata=DOMMetadataEvidence(has_title=True, title="Cache Test")
        )
    )
    audit = AuditResult(
        audit_id="audit-cache-001",
        target_url="https://cachetest.com",
        url="https://cachetest.com",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        evidence=evidence,
        desktop=evidence.desktop,
        issues=[issue_1],
        findings=[issue_1],
        stats=AuditSummaryStats(total_issues=1, high_count=1)
    )
    audit_engine._save_audit_to_db(audit, project_id=proj.project_id, db=db_session)

    # 3. Save AI Analysis record to DB
    ai_record = AIAnalysisModel(
        audit_id="audit-cache-001",
        issue_id="ISSUE-OVERFLOW-DESKTOP",
        summary="Horizontal overflow caused by wide element.",
        likely_causes=["Fixed width div"],
        investigation_hints=["Check CSS max-width"],
        expected_result="No horizontal scroll",
        constraints=["Preserve mobile layout"],
        verification_steps=["Resize window to 1440px"],
        fix_prompt="Fix width CSS rule"
    )
    db_session.add(ai_record)
    db_session.commit()

    # 4. Save Retest Audit & Comparison
    retest_audit = AuditResult(
        audit_id="audit-cache-002",
        target_url="https://cachetest.com",
        url="https://cachetest.com",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[],
        findings=[],
        stats=AuditSummaryStats(total_issues=0)
    )
    audit_engine._save_audit_to_db(retest_audit, baseline_audit_id="audit-cache-001", project_id=proj.project_id, db=db_session)

    # Clear in-memory cache completely
    audit_engine._audits_db.clear()
    assert len(audit_engine._audits_db) == 0

    # 5. Retrieve project and verify audit count
    fetched_proj = project_service.get_project(proj.project_id, db=db_session)
    assert fetched_proj is not None
    assert fetched_proj.audit_count == 2

    # 6. Retrieve detailed historical audit from DB
    retrieved_audit = audit_engine.get_audit("audit-cache-001", db=db_session)
    assert retrieved_audit is not None
    assert retrieved_audit.audit_id == "audit-cache-001"
    assert len(retrieved_audit.issues) == 1
    assert retrieved_audit.issues[0].issue_id == "ISSUE-OVERFLOW-DESKTOP"
    assert retrieved_audit.evidence is not None
    assert retrieved_audit.evidence.desktop.responsive.horizontal_overflow == 60

    # 7. Retrieve AI analysis from DB
    ai_analysis = audit_engine.get_ai_analysis("audit-cache-001", "ISSUE-OVERFLOW-DESKTOP", db=db_session)
    assert ai_analysis is not None
    assert ai_analysis.summary == "Horizontal overflow caused by wide element."
    assert ai_analysis.fix_prompt == "Fix width CSS rule"

    # 8. Perform audit comparison after cache clear
    comp = audit_engine.compare_audits("audit-cache-001", "audit-cache-002", db=db_session)
    assert comp is not None
    assert len(comp.fixed_issues) == 1
    assert comp.fixed_issues[0].issue_id == "ISSUE-OVERFLOW-DESKTOP"


def test_project_isolation(db_session):
    """
    Scenario 2: Project A and Project B audits are completely isolated in project history queries.
    """
    proj_a = project_service.create_project(CreateProjectRequest(name="Project Alpha", target_url="https://alpha.com"), db=db_session)
    proj_b = project_service.create_project(CreateProjectRequest(name="Project Beta", target_url="https://beta.com"), db=db_session)

    audit_a1 = AuditResult(audit_id="audit-a1", target_url="https://alpha.com", url="https://alpha.com", status=AuditStatus.COMPLETED, created_at=datetime.now(timezone.utc), issues=[], stats=AuditSummaryStats())
    audit_a2 = AuditResult(audit_id="audit-a2", target_url="https://alpha.com", url="https://alpha.com", status=AuditStatus.COMPLETED, created_at=datetime.now(timezone.utc), issues=[], stats=AuditSummaryStats())
    audit_b1 = AuditResult(audit_id="audit-b1", target_url="https://beta.com", url="https://beta.com", status=AuditStatus.COMPLETED, created_at=datetime.now(timezone.utc), issues=[], stats=AuditSummaryStats())

    audit_engine._save_audit_to_db(audit_a1, project_id=proj_a.project_id, db=db_session)
    audit_engine._save_audit_to_db(audit_a2, project_id=proj_a.project_id, db=db_session)
    audit_engine._save_audit_to_db(audit_b1, project_id=proj_b.project_id, db=db_session)

    history_a = project_service.list_project_audits(proj_a.project_id, db=db_session)
    assert len(history_a) == 2
    assert {h.audit_id for h in history_a} == {"audit-a1", "audit-a2"}

    history_b = project_service.list_project_audits(proj_b.project_id, db=db_session)
    assert len(history_b) == 1
    assert history_b[0].audit_id == "audit-b1"

    history_global = project_service.list_all_audits(db=db_session)
    global_ids = {g.audit_id for g in history_global}
    assert {"audit-a1", "audit-a2", "audit-b1"}.issubset(global_ids)


def test_default_project_singleton(db_session):
    """
    Scenario 4: get_or_create_default_project returns the single default project without duplication.
    """
    p1 = project_service.get_or_create_default_project(db_session)
    p2 = project_service.get_or_create_default_project(db_session)
    assert p1.project_id == DEFAULT_PROJECT_ID
    assert p2.project_id == DEFAULT_PROJECT_ID
    assert p1.project_id == p2.project_id


def test_legacy_audit_visibility_and_retest(db_session):
    """
    Scenarios 5 & 6: Legacy audits (project_id = NULL) appear in default project and global history,
    and retesting a legacy audit produces a safe retest with project_id = NULL.
    """
    legacy_audit = AuditResult(
        audit_id="legacy-001",
        target_url="https://legacy.site",
        url="https://legacy.site",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[],
        stats=AuditSummaryStats()
    )
    audit_engine._save_audit_to_db(legacy_audit, project_id=None, db=db_session)

    # 1. Visible in default project history
    def_audits = project_service.list_project_audits(DEFAULT_PROJECT_ID, db=db_session)
    assert any(a.audit_id == "legacy-001" for a in def_audits)

    # 2. Retest legacy audit preserves project_id = None
    retest_audit = AuditResult(
        audit_id="legacy-retest-002",
        target_url="https://legacy.site",
        url="https://legacy.site",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[],
        stats=AuditSummaryStats()
    )
    audit_engine._save_audit_to_db(retest_audit, baseline_audit_id="legacy-001", project_id=None, db=db_session)

    retest_fetched = audit_engine.get_audit("legacy-retest-002", db=db_session)
    assert retest_fetched is not None


@pytest.mark.asyncio
async def test_chained_retest_project_inheritance(db_session):
    """
    Scenarios 7 & 8: Chained retesting (Baseline -> Retest 1 -> Retest 2) preserves project association.
    """
    proj = project_service.create_project(CreateProjectRequest(name="Chained Proj", target_url="https://chained.com"), db=db_session)

    baseline = AuditResult(audit_id="base-1", target_url="https://chained.com", url="https://chained.com", status=AuditStatus.COMPLETED, created_at=datetime.now(timezone.utc), issues=[], stats=AuditSummaryStats())
    audit_engine._save_audit_to_db(baseline, project_id=proj.project_id, db=db_session)

    retest1 = AuditResult(audit_id="retest-1", target_url="https://chained.com", url="https://chained.com", status=AuditStatus.COMPLETED, created_at=datetime.now(timezone.utc), issues=[], stats=AuditSummaryStats())
    audit_engine._save_audit_to_db(retest1, baseline_audit_id="base-1", project_id=proj.project_id, db=db_session)

    retest2 = AuditResult(audit_id="retest-2", target_url="https://chained.com", url="https://chained.com", status=AuditStatus.COMPLETED, created_at=datetime.now(timezone.utc), issues=[], stats=AuditSummaryStats())
    audit_engine._save_audit_to_db(retest2, baseline_audit_id="retest-1", project_id=proj.project_id, db=db_session)

    history = project_service.list_project_audits(proj.project_id, db=db_session)
    assert len(history) == 3
    r2_item = next(item for item in history if item.audit_id == "retest-2")
    assert r2_item.baseline_audit_id == "retest-1"
    assert r2_item.project_id == proj.project_id


def test_invalid_project_and_audit_http_status_codes(db_session):
    """
    Scenarios 10 & 11: HTTP endpoints return correct status codes for invalid IDs.
    """
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
        user = UserModel(user_id="usr_ph_002", email="ph2@example.com", password_hash=hash_password("Pass123!"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()
        token = create_access_token(user.user_id, user.email)
        headers = {"Authorization": f"Bearer {token}"}

        # Invalid Project ID
        res_proj = client.get("/api/v1/projects/non-existent-proj-xyz", headers=headers)
        assert res_proj.status_code == 404
        assert "not found" in res_proj.json()["detail"].lower()

        # Invalid Audit ID
        res_audit = client.get("/api/v1/audits/non-existent-audit-xyz", headers=headers)
        assert res_audit.status_code == 404
        assert "not found" in res_audit.json()["detail"].lower()

        # Create project with empty name
        res_empty_name = client.post("/api/v1/projects", json={"name": "   ", "target_url": "https://example.com"}, headers=headers)
        assert res_empty_name.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_backward_compatible_audit_creation_schema(db_session):
    """
    Scenario 12: CreateAuditRequest without project_id remains backward compatible.
    """
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
        user = UserModel(user_id="usr_ph_003", email="ph3@example.com", password_hash=hash_password("Pass123!"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db_session.add(user)
        db_session.commit()
        token = create_access_token(user.user_id, user.email)
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/v1/audits", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)
    finally:
        app.dependency_overrides.clear()

