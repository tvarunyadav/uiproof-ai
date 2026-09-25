import pytest
from datetime import datetime, timezone
from app.services.audit import audit_engine
from app.schemas.audit import CreateAuditRequest, AuditStatus, AuditResult, AuditSummaryStats
from app.schemas.evidence import BrowserEvidence, ViewportAuditResult, BrowserViewport, PageMetadata, ResponsiveMetrics
from app.schemas.issue import Issue, IssueCategory, IssueSeverity
from app.db.models import AuditModel, IssueModel


@pytest.mark.asyncio
async def test_audit_and_issues_persistence(db_session):
    """
    Test 1, 3, 4, 5: Creates an audit, persists AuditModel and IssueModel to database,
    verifying stable issue IDs and foreign key links.
    """
    vp = BrowserViewport(name="Desktop", width=1440, height=900)
    page = PageMetadata(initial_url="https://example.com", final_url="https://example.com", title="Example", page_load_success=True)
    resp = ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0)
    vp_res = ViewportAuditResult(viewport=vp, page=page, responsive=resp)

    evidence = BrowserEvidence(
        url="https://example.com",
        timestamp=datetime.now(timezone.utc),
        desktop=vp_res,
        viewports_tested=[vp]
    )

    issue1 = Issue(
        issue_id="UI-CONSOLE-ERROR-DESKTOP-ABC123",
        category=IssueCategory.CONSOLE_ERROR,
        severity=IssueSeverity.HIGH,
        title="Uncaught ReferenceError",
        description="ReferenceError: foo is not defined",
        selector="window",
        viewport="Desktop",
        evidence_references=["script.js:42"]
    )

    issue2 = Issue(
        issue_id="UI-OVERFLOW-MOBILE",
        category=IssueCategory.RESPONSIVE,
        severity=IssueSeverity.HIGH,
        title="Mobile Horizontal Overflow",
        description="Scroll width exceeds client width",
        selector="body",
        viewport="Mobile",
        evidence_references=["Overflow: 25px"]
    )

    audit_result = AuditResult(
        audit_id="audit-persisted-001",
        target_url="https://example.com",
        url="https://example.com",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        desktop=vp_res,
        evidence=evidence,
        issues=[issue1, issue2],
        findings=[issue1, issue2],
        stats=AuditSummaryStats(total_issues=2, high_count=2)
    )

    # Save to database using db_session
    audit_engine._save_audit_to_db(audit_result, db=db_session)

    # Query DB models directly
    db_audit = db_session.query(AuditModel).filter_by(audit_id="audit-persisted-001").first()
    assert db_audit is not None
    assert db_audit.target_url == "https://example.com"
    assert db_audit.status == "completed"

    db_issues = db_session.query(IssueModel).filter_by(audit_id="audit-persisted-001").all()
    assert len(db_issues) == 2
    issue_ids = {i.issue_id for i in db_issues}
    assert "UI-CONSOLE-ERROR-DESKTOP-ABC123" in issue_ids
    assert "UI-OVERFLOW-MOBILE" in issue_ids


@pytest.mark.asyncio
async def test_persistence_survives_in_memory_clearing(db_session):
    """
    Test 2 & 8 (PROVE PERSISTENCE IS REAL):
    After creating an audit, clear the in-memory _audits_db dictionary,
    retrieve the audit again, and verify that the data comes directly from the database.
    """
    vp = BrowserViewport(name="Desktop", width=1440, height=900)
    page = PageMetadata(initial_url="https://test-persist.com", final_url="https://test-persist.com", title="Test", page_load_success=True)
    resp = ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0)
    vp_res = ViewportAuditResult(viewport=vp, page=page, responsive=resp)

    issue = Issue(
        issue_id="UI-MISSING-TITLE-DESKTOP",
        category=IssueCategory.SEO,
        severity=IssueSeverity.MEDIUM,
        title="Missing Title",
        description="Page title tag missing",
        selector="head > title",
        viewport="Desktop"
    )

    audit_result = AuditResult(
        audit_id="audit-db-only-999",
        target_url="https://test-persist.com",
        url="https://test-persist.com",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[issue],
        findings=[issue],
        stats=AuditSummaryStats(total_issues=1)
    )

    # Save to DB
    audit_engine._save_audit_to_db(audit_result, db=db_session)

    # CLEAR IN-MEMORY DICTIONARY TO PROVE DATABASE READ PATH
    audit_engine._audits_db.clear()
    assert "audit-db-only-999" not in audit_engine._audits_db

    # Retrieve from DB via get_audit
    retrieved = audit_engine.get_audit("audit-db-only-999", db=db_session)

    assert retrieved is not None
    assert retrieved.audit_id == "audit-db-only-999"
    assert retrieved.target_url == "https://test-persist.com"
    assert len(retrieved.issues) == 1
    assert retrieved.issues[0].issue_id == "UI-MISSING-TITLE-DESKTOP"
    assert retrieved.issues[0].category == IssueCategory.SEO


@pytest.mark.asyncio
async def test_retest_and_comparison_with_db(db_session):
    """
    Test 7: Retest and comparison flow with baseline and retest persisted in DB.
    """
    issue1 = Issue(
        issue_id="UI-BROKEN-LINK-DESKTOP-111",
        category=IssueCategory.BROKEN_RESOURCE,
        severity=IssueSeverity.MEDIUM,
        title="Broken Link",
        description="Link returns 404",
        viewport="Desktop"
    )
    baseline_result = AuditResult(
        audit_id="baseline-db-001",
        target_url="https://site.org",
        url="https://site.org",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[issue1],
        findings=[issue1],
        stats=AuditSummaryStats(total_issues=1)
    )
    audit_engine._save_audit_to_db(baseline_result, db=db_session)

    issue2 = Issue(
        issue_id="UI-BROKEN-LINK-DESKTOP-111",
        category=IssueCategory.BROKEN_RESOURCE,
        severity=IssueSeverity.MEDIUM,
        title="Broken Link",
        description="Link returns 404",
        viewport="Desktop"
    )
    retest_result = AuditResult(
        audit_id="retest-db-002",
        target_url="https://site.org",
        url="https://site.org",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[issue2],
        findings=[issue2],
        stats=AuditSummaryStats(total_issues=1)
    )
    audit_engine._save_audit_to_db(retest_result, baseline_audit_id="baseline-db-001", db=db_session)

    # Clear in-memory state
    audit_engine._audits_db.clear()

    # Perform comparison reading from DB
    comparison = audit_engine.compare_audits(baseline_id="baseline-db-001", new_id="retest-db-002", db=db_session)
    assert comparison is not None
    assert comparison.baseline_audit_id == "baseline-db-001"
    assert comparison.new_audit_id == "retest-db-002"
    assert len(comparison.remaining_issues) == 1
    assert comparison.remaining_issues[0].issue_id == "UI-BROKEN-LINK-DESKTOP-111"
    assert len(comparison.fixed_issues) == 0
