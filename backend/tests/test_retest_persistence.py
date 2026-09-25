import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from app.services.audit import audit_engine, create_deterministic_findings
from app.schemas.audit import AuditResult, AuditStatus, AuditSummaryStats
from app.schemas.evidence import BrowserEvidence, ViewportAuditResult, PageMetadata, ResponsiveMetrics, BrowserViewport
from app.schemas.issue import Issue, IssueCategory, IssueSeverity
from app.db.models import AuditModel, IssueModel


@pytest.mark.asyncio
async def test_retest_without_audits_db_cache(db_session):
    """
    Test 1, 2, 3, 8:
    1. Create and persist baseline audit to DB.
    2. Clear in-memory _audits_db cache.
    3. Call retest_audit(baseline_id) with mocked browser runner.
    4. Verify baseline audit was retrieved from DB.
    5. Verify new retest audit is persisted in DB with baseline_audit_id.
    6. Verify retest issues are persisted in DB.
    7. Clear _audits_db again and retrieve both from DB.
    """
    vp = BrowserViewport(name="Desktop", width=1440, height=900)
    page = PageMetadata(initial_url="https://retest-site.org", final_url="https://retest-site.org", title="Baseline Site", page_load_success=True)
    resp = ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0)
    vp_res = ViewportAuditResult(viewport=vp, page=page, responsive=resp)

    issue_baseline = Issue(
        issue_id="UI-MISSING-TITLE-DESKTOP",
        category=IssueCategory.SEO,
        severity=IssueSeverity.MEDIUM,
        title="Missing Title",
        description="Missing title tag on desktop",
        viewport="Desktop"
    )

    baseline_audit = AuditResult(
        audit_id="baseline-db-999",
        target_url="https://retest-site.org",
        url="https://retest-site.org",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        desktop=vp_res,
        issues=[issue_baseline],
        findings=[issue_baseline],
        stats=AuditSummaryStats(total_issues=1)
    )

    # 1. Persist baseline to DB
    audit_engine._save_audit_to_db(baseline_audit, db=db_session)

    # 2. Clear in-memory state
    audit_engine._audits_db.clear()
    assert "baseline-db-999" not in audit_engine._audits_db

    # 3. Perform retest using mocked evidence collection
    mock_retest_evidence = BrowserEvidence(
        url="https://retest-site.org",
        timestamp=datetime.now(timezone.utc),
        desktop=vp_res,
        viewports_tested=[vp]
    )

    issue_retest_new = Issue(
        issue_id="UI-CONSOLE-ERROR-DESKTOP-555666",
        category=IssueCategory.CONSOLE_ERROR,
        severity=IssueSeverity.HIGH,
        title="Console Error",
        description="New console error on retest",
        viewport="Desktop"
    )

    with patch.object(audit_engine.browser_runner, "collect_evidence", new_callable=AsyncMock) as mock_collect, \
         patch("app.services.audit.create_deterministic_findings", return_value=[issue_baseline, issue_retest_new]):
        mock_collect.return_value = mock_retest_evidence

        retest_result, comparison = await audit_engine.retest_audit("baseline-db-999", db=db_session)

        assert retest_result is not None
        assert retest_result.target_url == "https://retest-site.org"

        # 4. Check DB for retest audit record
        db_retest_audit = db_session.query(AuditModel).filter_by(audit_id=retest_result.audit_id).first()
        assert db_retest_audit is not None
        assert db_retest_audit.baseline_audit_id == "baseline-db-999"
        assert db_retest_audit.target_url == "https://retest-site.org"

        # 5. Clear in-memory state again
        audit_engine._audits_db.clear()

        # 6. Retrieve both audits from DB
        fetched_baseline = audit_engine.get_audit("baseline-db-999", db=db_session)
        fetched_retest = audit_engine.get_audit(retest_result.audit_id, db=db_session)

        assert fetched_baseline is not None
        assert fetched_retest is not None
        assert len(fetched_baseline.issues) == 1
        assert len(fetched_retest.issues) == 2


@pytest.mark.asyncio
async def test_comparison_without_audits_db_cache(db_session):
    """
    Test 4, 5, 6, 7, 9, 10:
    1. Create baseline audit with UI-ISSUE-A and UI-ISSUE-B in DB.
    2. Create retest audit with UI-ISSUE-B and UI-ISSUE-C in DB.
    3. Clear _audits_db cache.
    4. Call compare_audits(baseline_id, retest_id).
    5. Verify FIXED = UI-ISSUE-A, REMAINING = UI-ISSUE-B, NEW = UI-ISSUE-C.
    """
    issue_a = Issue(
        issue_id="UI-ISSUE-A",
        category=IssueCategory.LAYOUT,
        severity=IssueSeverity.HIGH,
        title="Issue A",
        description="Issue A description",
        viewport="Desktop"
    )
    issue_b = Issue(
        issue_id="UI-ISSUE-B",
        category=IssueCategory.RESPONSIVE,
        severity=IssueSeverity.MEDIUM,
        title="Issue B",
        description="Issue B description",
        viewport="Mobile"
    )
    issue_c = Issue(
        issue_id="UI-ISSUE-C",
        category=IssueCategory.SEO,
        severity=IssueSeverity.LOW,
        title="Issue C",
        description="Issue C description",
        viewport="Desktop"
    )

    baseline_audit = AuditResult(
        audit_id="baseline-comp-001",
        target_url="https://comp.example.com",
        url="https://comp.example.com",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[issue_a, issue_b],
        findings=[issue_a, issue_b],
        stats=AuditSummaryStats(total_issues=2)
    )
    audit_engine._save_audit_to_db(baseline_audit, db=db_session)

    retest_audit = AuditResult(
        audit_id="retest-comp-002",
        target_url="https://comp.example.com",
        url="https://comp.example.com",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[issue_b, issue_c],
        findings=[issue_b, issue_c],
        stats=AuditSummaryStats(total_issues=2)
    )
    audit_engine._save_audit_to_db(retest_audit, baseline_audit_id="baseline-comp-001", db=db_session)

    # CLEAR IN-MEMORY DICTIONARY
    audit_engine._audits_db.clear()
    assert "baseline-comp-001" not in audit_engine._audits_db
    assert "retest-comp-002" not in audit_engine._audits_db

    # Call compare_audits directly reading from DB
    comparison = audit_engine.compare_audits(baseline_id="baseline-comp-001", new_id="retest-comp-002", db=db_session)

    assert comparison is not None
    assert comparison.baseline_audit_id == "baseline-comp-001"
    assert comparison.new_audit_id == "retest-comp-002"

    fixed_ids = [i.issue_id for i in comparison.fixed_issues]
    remaining_ids = [i.issue_id for i in comparison.remaining_issues]
    new_ids = [i.issue_id for i in comparison.new_issues]

    assert fixed_ids == ["UI-ISSUE-A"]
    assert remaining_ids == ["UI-ISSUE-B"]
    assert new_ids == ["UI-ISSUE-C"]
