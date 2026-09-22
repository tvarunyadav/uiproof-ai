import pytest
from app.schemas.issue import generate_stable_issue_id, Issue, IssueCategory, IssueSeverity
from app.schemas.audit import CreateAuditRequest, AuditStatus

def test_stable_issue_id_generation():
    id1 = generate_stable_issue_id("layout", "#submit-btn", "Button overlap")
    id2 = generate_stable_issue_id("layout", "#submit-btn", "Button overlap")
    id3 = generate_stable_issue_id("layout", "#submit-btn", "Different title")

    assert id1.startswith("ISSUE-LAY-")
    assert id1 == id2, "Identical issue inputs must yield identical stable Issue IDs"
    assert id1 != id3, "Different titles must yield different stable Issue IDs"

def test_issue_model_validation():
    issue = Issue(
        issue_id=generate_stable_issue_id("console_error", "window", "Uncaught TypeError"),
        category=IssueCategory.CONSOLE_ERROR,
        severity=IssueSeverity.HIGH,
        title="Uncaught TypeError in bundle.js",
        description="Cannot read properties of null (reading 'map')",
        selector="window"
    )
    assert issue.severity == IssueSeverity.HIGH
    assert issue.category == IssueCategory.CONSOLE_ERROR

def test_audit_request_validation():
    req = CreateAuditRequest(url="https://example.com", viewports=["desktop", "mobile"])
    assert req.url == "https://example.com"
    assert len(req.viewports) == 2
