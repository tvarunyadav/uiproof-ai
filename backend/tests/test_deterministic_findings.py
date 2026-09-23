from datetime import datetime, timezone
from app.schemas.evidence import (
    BrowserEvidence,
    BrowserViewport,
    ConsoleLogEntry,
    NetworkFailure,
    ResponsiveMetrics,
    PageMetadata,
    ViewportAuditResult,
)
from app.services.audit import create_deterministic_findings
from app.schemas.issue import IssueCategory, IssueSeverity


def test_deterministic_finding_generation():
    vp = BrowserViewport(name="Mobile", width=390, height=844, device_scale_factor=2.0)
    
    mobile_res = ViewportAuditResult(
        viewport=vp,
        page=PageMetadata(
            initial_url="https://example.com",
            final_url="https://example.com",
            title="Example Site",
            http_status=200,
            page_load_success=True
        ),
        console_errors=[
            ConsoleLogEntry(
                timestamp=datetime.now(timezone.utc),
                level="error",
                text="Uncaught TypeError: Cannot read property 'id' of null",
                location="app.js:42"
            )
        ],
        network_failures=[
            NetworkFailure(
                timestamp=datetime.now(timezone.utc),
                url="https://example.com/api/missing",
                method="GET",
                status_code=404,
                error_text="HTTP 404 Not Found"
            )
        ],
        responsive=ResponsiveMetrics(
            viewport_width=390,
            viewport_height=844,
            document_scroll_width=450,
            document_client_width=390,
            horizontal_overflow=60
        )
    )

    evidence = BrowserEvidence(
        url="https://example.com",
        timestamp=datetime.now(timezone.utc),
        mobile=mobile_res,
        viewports_tested=[vp]
    )

    findings = create_deterministic_findings(evidence)

    # Should detect 3 deterministic findings: 1 console error, 1 network failure, 1 mobile overflow
    assert len(findings) == 3

    categories = [f.category for f in findings]
    assert IssueCategory.CONSOLE_ERROR in categories
    assert IssueCategory.NETWORK_FAILURE in categories
    assert IssueCategory.RESPONSIVE in categories or IssueCategory.LAYOUT in categories


    overflow_issue = next(f for f in findings if f.category in (IssueCategory.RESPONSIVE, IssueCategory.LAYOUT))
    assert overflow_issue.severity == IssueSeverity.HIGH
    assert "60px" in overflow_issue.description
