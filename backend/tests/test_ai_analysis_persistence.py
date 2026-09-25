import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from app.services.audit import audit_engine
from app.schemas.audit import AuditResult, AuditStatus, AuditSummaryStats
from app.schemas.issue import Issue, IssueCategory, IssueSeverity
from app.schemas.evidence import BrowserEvidence, ViewportAuditResult, PageMetadata, ResponsiveMetrics
from app.schemas.ai import AIAnalysisDetails
from app.db.models import AIAnalysisModel, IssueModel


@pytest.mark.asyncio
async def test_ai_analysis_persistence_and_no_recall(db_session):
    """
    Test 1-9: Proves AI analysis persistence is real:
    1. Create an audit with a deterministic issue and save to DB.
    2. Run AI analysis with a mock provider.
    3. Verify AIAnalysisModel row is created in DB.
    4. Clear in-memory _audits_db.
    5. Retrieve AI analysis again from DB.
    6. Verify reconstructed response matches original result.
    7. Verify LLM provider was NOT called a second time.
    """
    vp = ViewportAuditResult(
        viewport={"name": "Mobile", "width": 390, "height": 844, "device_scale_factor": 2.0},
        page=PageMetadata(initial_url="https://test.com", final_url="https://test.com/", title="Test Site", http_status=200, page_load_success=True),
        responsive=ResponsiveMetrics(viewport_width=390, viewport_height=844, document_scroll_width=428, document_client_width=390, horizontal_overflow=38)
    )
    evidence = BrowserEvidence(url="https://test.com", timestamp=datetime.now(timezone.utc), mobile=vp)
    issue = Issue(
        issue_id="UI-OVERFLOW-MOBILE",
        category=IssueCategory.RESPONSIVE,
        severity=IssueSeverity.HIGH,
        title="Mobile Horizontal Overflow",
        description="Scroll width exceeds client width.",
        selector="body",
        viewport="Mobile"
    )

    audit_result = AuditResult(
        audit_id="audit-ai-persist-100",
        target_url="https://test.com",
        url="https://test.com",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        evidence=evidence,
        issues=[issue],
        findings=[issue],
        stats=AuditSummaryStats(total_issues=1)
    )

    # 1. Save audit to DB
    audit_engine._save_audit_to_db(audit_result, db=db_session)

    mock_analysis = AIAnalysisDetails(
        summary="Horizontal overflow on mobile viewports.",
        likely_causes=["Unconstrained container width"],
        investigation_hints=["Inspect element bounds in DevTools"],
        expected_result="Document scrollWidth matches viewport width",
        constraints=["Preserve desktop layout"],
        verification_steps=["Resize viewport to 390px and check scrollbar"],
        fix_prompt="Set max-width: 100% on body"
    )

    # 2. Run AI analysis flow with mock provider
    with patch.object(audit_engine.ai_provider, "analyze_issue", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_analysis

        response_1 = await audit_engine.analyze_issue("audit-ai-persist-100", "UI-OVERFLOW-MOBILE", db=db_session)

        assert response_1 is not None
        assert response_1.analysis.summary == mock_analysis.summary
        assert mock_analyze.call_count == 1

    # 3. Verify AIAnalysisModel row exists in database
    db_ai_row = (
        db_session.query(AIAnalysisModel)
        .filter_by(audit_id="audit-ai-persist-100", issue_id="UI-OVERFLOW-MOBILE")
        .first()
    )
    assert db_ai_row is not None
    assert db_ai_row.summary == "Horizontal overflow on mobile viewports."
    assert db_ai_row.fix_prompt == "Set max-width: 100% on body"

    # 4. Verify IssueModel updated in database
    db_issue_row = (
        db_session.query(IssueModel)
        .filter_by(audit_id="audit-ai-persist-100", issue_id="UI-OVERFLOW-MOBILE")
        .first()
    )
    assert db_issue_row is not None
    assert "Horizontal overflow" in db_issue_row.root_cause_analysis
    assert db_issue_row.recommended_fix == "Set max-width: 100% on body"

    # 5. Clear in-memory cache to prove DB read path
    audit_engine._audits_db.clear()
    assert "audit-ai-persist-100" not in audit_engine._audits_db

    # 6. Retrieve AI analysis again — LLM provider should NOT be called
    with patch.object(audit_engine.ai_provider, "analyze_issue", new_callable=AsyncMock) as mock_analyze_2:
        response_2 = await audit_engine.analyze_issue("audit-ai-persist-100", "UI-OVERFLOW-MOBILE", db=db_session)

        # Provider must NOT have been called on second retrieval
        assert mock_analyze_2.call_count == 0

        # Reconstructed response must match original persisted result
        assert response_2.audit_id == "audit-ai-persist-100"
        assert response_2.issue_id == "UI-OVERFLOW-MOBILE"
        assert response_2.analysis.summary == mock_analysis.summary
        assert response_2.analysis.fix_prompt == mock_analysis.fix_prompt
        assert response_2.analysis.likely_causes == mock_analysis.likely_causes
        assert response_2.issue.recommended_fix == mock_analysis.fix_prompt
