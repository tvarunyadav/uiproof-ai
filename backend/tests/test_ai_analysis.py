import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from app.schemas.audit import AuditResult, AuditStatus, AuditSummaryStats
from app.schemas.issue import Issue, IssueCategory, IssueSeverity
from app.schemas.evidence import BrowserEvidence, ViewportAuditResult, PageMetadata, ResponsiveMetrics
from app.schemas.ai import AIAnalysisDetails, IssueAnalysisResponse
from app.services.audit import audit_engine
from app.services.ai.interface import AINotConfiguredError, AIProviderError, BaseLLMProvider
from app.services.ai.openai_provider import OpenAILLMProvider


def setup_sample_audit():
    """Helper to populate in-memory audit DB with a sample audit and deterministic issue."""
    audit_id = "test-audit-ai-123"
    issue = Issue(
        issue_id="UI-OVERFLOW-MOBILE",
        category=IssueCategory.RESPONSIVE,
        severity=IssueSeverity.HIGH,
        title="Mobile Horizontal Overflow",
        description="Document scroll width (428px) exceeds client width (390px) by 38px on Mobile.",
        selector="body",
        viewport="Mobile",
        evidence_references=["Viewport: 390px, ScrollWidth: 428px, Overflow: 38px"]
    )
    vp_mobile = ViewportAuditResult(
        viewport={"name": "Mobile", "width": 390, "height": 844, "device_scale_factor": 2.0},
        page=PageMetadata(initial_url="https://example.com", final_url="https://example.com/", title="Test Site", http_status=200, page_load_success=True),
        responsive=ResponsiveMetrics(viewport_width=390, viewport_height=844, document_scroll_width=428, document_client_width=390, horizontal_overflow=38)
    )
    evidence = BrowserEvidence(
        url="https://example.com",
        timestamp=datetime.now(timezone.utc),
        mobile=vp_mobile
    )
    audit = AuditResult(
        audit_id=audit_id,
        target_url="https://example.com",
        url="https://example.com",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        evidence=evidence,
        issues=[issue],
        findings=[issue],
        stats=AuditSummaryStats(total_issues=1, high_count=1)
    )
    audit_engine._audits_db[audit_id] = audit
    return audit_id, issue.issue_id


@pytest.mark.asyncio
async def test_ai_analysis_missing_api_key(async_client):
    audit_id, issue_id = setup_sample_audit()
    with patch.object(audit_engine.ai_provider, "analyze_issue", side_effect=AINotConfiguredError("AI API key is not configured.")):
        res = await async_client.post(f"/api/v1/audits/{audit_id}/issues/{issue_id}/analyze")
        assert res.status_code == 503
        data = res.json()
        assert data["detail"]["error"] == "AI_NOT_CONFIGURED"
        assert "API key is not configured" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_ai_analysis_provider_error(async_client):
    audit_id, issue_id = setup_sample_audit()
    with patch.object(audit_engine.ai_provider, "analyze_issue", side_effect=AIProviderError("LLM Provider connection timeout")):
        res = await async_client.post(f"/api/v1/audits/{audit_id}/issues/{issue_id}/analyze")
        assert res.status_code == 503
        data = res.json()
        assert data["detail"]["error"] == "AI_PROVIDER_ERROR"
        assert "connection timeout" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_ai_analysis_unknown_audit(async_client):
    res = await async_client.post("/api/v1/audits/nonexistent-audit-999/issues/UI-OVERFLOW-MOBILE/analyze")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_ai_analysis_unknown_issue(async_client):
    audit_id, _ = setup_sample_audit()
    res = await async_client.post(f"/api/v1/audits/{audit_id}/issues/NONEXISTENT-ISSUE-ID/analyze")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_ai_analysis_success_mocked_provider(async_client):
    audit_id, issue_id = setup_sample_audit()

    mock_analysis = AIAnalysisDetails(
        summary="Horizontal overflow on mobile caused by fixed width element exceeding 390px viewport width.",
        likely_causes=[
            "Fixed width CSS container set to 428px or 100vw + padding.",
            "Unconstrained hero image or pre/code block."
        ],
        investigation_hints=["Inspect element bounds in DevTools around 390px breakpoint."],
        expected_result="Document scrollWidth equals 390px with zero horizontal scroll.",
        constraints=["Preserve desktop grid layout at 1440px viewport."],
        verification_steps=["Resize viewport to 390px and check document.documentElement.scrollWidth == 390."],
        fix_prompt="Investigate root element exceeding 390px viewport width causing 38px overflow. Do NOT use overflow-x: hidden."
    )

    with patch.object(audit_engine.ai_provider, "analyze_issue", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_analysis

        res = await async_client.post(f"/api/v1/audits/{audit_id}/issues/{issue_id}/analyze")
        assert res.status_code == 200

        data = res.json()
        assert data["audit_id"] == audit_id
        assert data["issue_id"] == issue_id

        # Deterministic identity MUST remain unchanged
        assert data["issue"]["issue_id"] == "UI-OVERFLOW-MOBILE"
        assert data["issue"]["category"] == "responsive"
        assert data["issue"]["severity"] == "high"

        # AI analysis payload structure check
        assert data["analysis"]["summary"] == mock_analysis.summary
        assert len(data["analysis"]["likely_causes"]) == 2
        assert "Do NOT use overflow-x: hidden" in data["analysis"]["fix_prompt"]

        # Enriched fields on issue object
        assert mock_analysis.summary in data["issue"]["root_cause_analysis"]
        assert data["issue"]["recommended_fix"] == mock_analysis.fix_prompt


@pytest.mark.asyncio
async def test_openai_provider_raises_not_configured_when_key_empty():
    provider = OpenAILLMProvider(api_key="")
    sample_issue = Issue(
        issue_id="UI-MISSING-META-DESKTOP",
        category=IssueCategory.SEO,
        severity=IssueSeverity.LOW,
        title="Missing Meta Description",
        description="Missing meta description tag."
    )
    with pytest.raises(AINotConfiguredError):
        await provider.analyze_issue(sample_issue)
