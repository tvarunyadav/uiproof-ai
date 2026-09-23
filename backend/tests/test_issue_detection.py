import pytest
from datetime import datetime, timezone
from app.schemas.evidence import (
    BrowserEvidence,
    BrowserViewport,
    ConsoleLogEntry,
    NetworkFailure,
    ResponsiveMetrics,
    PageMetadata,
    ViewportAuditResult,
    BrokenImageEvidence,
    BrokenLinkEvidence,
    DOMMetadataEvidence,
    AccessibilityViolation,
)
from app.schemas.issue import (
    IssueCategory,
    IssueSeverity,
    generate_deterministic_issue_id,
)
from app.services.audit import create_deterministic_findings


def test_1_no_overflow():
    vp = BrowserViewport(name="Desktop", width=1440, height=900, device_scale_factor=1.0)
    vp_res = ViewportAuditResult(
        viewport=vp,
        page=PageMetadata(initial_url="https://example.com", final_url="https://example.com/", title="Clean Site", http_status=200, page_load_success=True),
        responsive=ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0),
        dom_metadata=DOMMetadataEvidence(title="Clean Site", has_title=True, meta_description="Site description", has_meta_description=True)
    )
    evidence = BrowserEvidence(url="https://example.com", timestamp=datetime.now(timezone.utc), desktop=vp_res)

    findings = create_deterministic_findings(evidence)
    overflow_issues = [f for f in findings if f.category == IssueCategory.RESPONSIVE or f.category == IssueCategory.LAYOUT]
    assert len(overflow_issues) == 0


def test_2_horizontal_overflow():
    vp = BrowserViewport(name="Mobile", width=390, height=844, device_scale_factor=2.0)
    vp_res = ViewportAuditResult(
        viewport=vp,
        page=PageMetadata(initial_url="https://example.com", final_url="https://example.com/", title="Overflow Site", http_status=200, page_load_success=True),
        responsive=ResponsiveMetrics(viewport_width=390, viewport_height=844, document_scroll_width=428, document_client_width=390, horizontal_overflow=38),
        dom_metadata=DOMMetadataEvidence(title="Overflow Site", has_title=True, meta_description="Desc", has_meta_description=True)
    )
    evidence = BrowserEvidence(url="https://example.com", timestamp=datetime.now(timezone.utc), mobile=vp_res)

    findings = create_deterministic_findings(evidence)
    overflow_issue = next(f for f in findings if f.category == IssueCategory.RESPONSIVE)

    assert overflow_issue.issue_id == "UI-OVERFLOW-MOBILE"
    assert overflow_issue.severity == IssueSeverity.HIGH
    assert "38px" in overflow_issue.description


def test_3_console_error():
    vp = BrowserViewport(name="Desktop", width=1440, height=900, device_scale_factor=1.0)
    vp_res = ViewportAuditResult(
        viewport=vp,
        page=PageMetadata(initial_url="https://example.com", final_url="https://example.com/", title="Test", http_status=200, page_load_success=True),
        console_errors=[
            ConsoleLogEntry(timestamp=datetime.now(timezone.utc), level="error", text="Uncaught TypeError: Cannot read property 'map' of undefined", location="bundle.js:105")
        ],
        responsive=ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0),
        dom_metadata=DOMMetadataEvidence(title="Test", has_title=True, meta_description="Desc", has_meta_description=True)
    )
    evidence = BrowserEvidence(url="https://example.com", timestamp=datetime.now(timezone.utc), desktop=vp_res)

    findings = create_deterministic_findings(evidence)
    console_issue = next(f for f in findings if f.category == IssueCategory.CONSOLE_ERROR)

    assert console_issue.severity == IssueSeverity.HIGH
    assert "Uncaught TypeError" in console_issue.description
    assert console_issue.selector == "bundle.js:105"


def test_4_network_failure():
    vp = BrowserViewport(name="Desktop", width=1440, height=900, device_scale_factor=1.0)
    vp_res = ViewportAuditResult(
        viewport=vp,
        page=PageMetadata(initial_url="https://example.com", final_url="https://example.com/", title="Test", http_status=200, page_load_success=True),
        network_failures=[
            NetworkFailure(timestamp=datetime.now(timezone.utc), url="https://example.com/api/data", method="POST", status_code=500, error_text="HTTP 500 Internal Server Error")
        ],
        responsive=ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0),
        dom_metadata=DOMMetadataEvidence(title="Test", has_title=True, meta_description="Desc", has_meta_description=True)
    )
    evidence = BrowserEvidence(url="https://example.com", timestamp=datetime.now(timezone.utc), desktop=vp_res)

    findings = create_deterministic_findings(evidence)
    net_issue = next(f for f in findings if f.category == IssueCategory.NETWORK_FAILURE)

    assert net_issue.severity == IssueSeverity.HIGH
    assert "500" in net_issue.description


def test_5_broken_image():
    vp = BrowserViewport(name="Mobile", width=390, height=844, device_scale_factor=2.0)
    vp_res = ViewportAuditResult(
        viewport=vp,
        page=PageMetadata(initial_url="https://example.com", final_url="https://example.com/", title="Test", http_status=200, page_load_success=True),
        broken_images=[
            BrokenImageEvidence(src="https://example.com/missing-hero.jpg", alt="Hero banner", selector="#hero-img", error_reason="naturalWidth is 0")
        ],
        responsive=ResponsiveMetrics(viewport_width=390, viewport_height=844, document_scroll_width=390, document_client_width=390, horizontal_overflow=0),
        dom_metadata=DOMMetadataEvidence(title="Test", has_title=True, meta_description="Desc", has_meta_description=True)
    )
    evidence = BrowserEvidence(url="https://example.com", timestamp=datetime.now(timezone.utc), mobile=vp_res)

    findings = create_deterministic_findings(evidence)
    img_issue = next(f for f in findings if f.category == IssueCategory.BROKEN_RESOURCE and "Broken Image" in f.title)

    assert img_issue.severity == IssueSeverity.MEDIUM
    assert img_issue.selector == "#hero-img"
    assert "missing-hero.jpg" in img_issue.description


def test_6_missing_title():
    vp = BrowserViewport(name="Desktop", width=1440, height=900, device_scale_factor=1.0)
    vp_res = ViewportAuditResult(
        viewport=vp,
        page=PageMetadata(initial_url="https://example.com", final_url="https://example.com/", title="", http_status=200, page_load_success=True),
        responsive=ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0),
        dom_metadata=DOMMetadataEvidence(title="", has_title=False, meta_description="Desc", has_meta_description=True)
    )
    evidence = BrowserEvidence(url="https://example.com", timestamp=datetime.now(timezone.utc), desktop=vp_res)

    findings = create_deterministic_findings(evidence)
    title_issue = next(f for f in findings if f.issue_id == "UI-MISSING-TITLE-DESKTOP")

    assert title_issue.severity == IssueSeverity.MEDIUM
    assert title_issue.category == IssueCategory.SEO


def test_7_missing_meta_description():
    vp = BrowserViewport(name="Desktop", width=1440, height=900, device_scale_factor=1.0)
    vp_res = ViewportAuditResult(
        viewport=vp,
        page=PageMetadata(initial_url="https://example.com", final_url="https://example.com/", title="Site Title", http_status=200, page_load_success=True),
        responsive=ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0),
        dom_metadata=DOMMetadataEvidence(title="Site Title", has_title=True, meta_description="", has_meta_description=False)
    )
    evidence = BrowserEvidence(url="https://example.com", timestamp=datetime.now(timezone.utc), desktop=vp_res)

    findings = create_deterministic_findings(evidence)
    meta_issue = next(f for f in findings if f.issue_id == "UI-MISSING-META-DESKTOP")

    assert meta_issue.severity == IssueSeverity.LOW
    assert meta_issue.category == IssueCategory.SEO


def test_8_basic_accessibility():
    vp = BrowserViewport(name="Mobile", width=390, height=844, device_scale_factor=2.0)
    vp_res = ViewportAuditResult(
        viewport=vp,
        page=PageMetadata(initial_url="https://example.com", final_url="https://example.com/", title="Site Title", http_status=200, page_load_success=True),
        responsive=ResponsiveMetrics(viewport_width=390, viewport_height=844, document_scroll_width=390, document_client_width=390, horizontal_overflow=0),
        dom_metadata=DOMMetadataEvidence(title="Site Title", has_title=True, meta_description="Desc", has_meta_description=True),
        a11y_violations=[
            AccessibilityViolation(rule_id="missing-alt", impact="medium", selector="img:nth-of-type(2)", description="Basic accessibility check: Image element is missing an alt attribute.", html_snippet="<img src='logo.png'>"),
            AccessibilityViolation(rule_id="unlabeled-form-control", impact="medium", selector="#search-input", description="Basic accessibility check: Form input control has no associated <label> or aria-label attribute.", html_snippet="<input id='search-input'>")
        ]
    )
    evidence = BrowserEvidence(url="https://example.com", timestamp=datetime.now(timezone.utc), mobile=vp_res)

    findings = create_deterministic_findings(evidence)
    a11y_issues = [f for f in findings if f.category == IssueCategory.ACCESSIBILITY]

    assert len(a11y_issues) == 2
    assert any("missing-alt" in f.title for f in a11y_issues)
    assert any("unlabeled-form-control" in f.title for f in a11y_issues)
    assert all("Basic accessibility check" in f.description for f in a11y_issues)


def test_9_stable_issue_ids():
    id1 = generate_deterministic_issue_id("OVERFLOW", "Mobile")
    id2 = generate_deterministic_issue_id("OVERFLOW", "Mobile")
    id3 = generate_deterministic_issue_id("BROKEN-IMAGE", "Desktop", "https://example.com/a.png")
    id4 = generate_deterministic_issue_id("BROKEN-IMAGE", "Desktop", "https://example.com/a.png")

    assert id1 == "UI-OVERFLOW-MOBILE"
    assert id1 == id2
    assert id3 == id4
    assert id3.startswith("UI-BROKEN-IMAGE-DESKTOP-")


def test_10_deduplication():
    vp = BrowserViewport(name="Desktop", width=1440, height=900, device_scale_factor=1.0)
    vp_res = ViewportAuditResult(
        viewport=vp,
        page=PageMetadata(initial_url="https://example.com", final_url="https://example.com/", title="Test", http_status=200, page_load_success=True),
        console_errors=[
            ConsoleLogEntry(timestamp=datetime.now(timezone.utc), level="error", text="Identical error message", location="script.js:10"),
            ConsoleLogEntry(timestamp=datetime.now(timezone.utc), level="error", text="Identical error message", location="script.js:10")
        ],
        responsive=ResponsiveMetrics(viewport_width=1440, viewport_height=900, document_scroll_width=1440, document_client_width=1440, horizontal_overflow=0),
        dom_metadata=DOMMetadataEvidence(title="Test", has_title=True, meta_description="Desc", has_meta_description=True)
    )
    evidence = BrowserEvidence(url="https://example.com", timestamp=datetime.now(timezone.utc), desktop=vp_res)

    findings = create_deterministic_findings(evidence)
    console_issues = [f for f in findings if f.category == IssueCategory.CONSOLE_ERROR]

    # Duplicate identical console error should be deduplicated to 1
    assert len(console_issues) == 1
