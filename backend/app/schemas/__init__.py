"""UIProof AI Schemas Package."""
from app.schemas.evidence import (
    BrowserViewport,
    ConsoleLogEntry,
    NetworkFailure,
    LayoutIssue,
    AccessibilityIssue,
    PerformanceMetric,
    BrowserEvidence,
)
from app.schemas.issue import (
    IssueSeverity,
    IssueCategory,
    Issue,
    generate_stable_issue_id,
)
from app.schemas.audit import (
    AuditStatus,
    CreateAuditRequest,
    AuditResult,
    AuditComparison,
    DeveloperFixPrompt,
)

__all__ = [
    "BrowserViewport",
    "ConsoleLogEntry",
    "NetworkFailure",
    "LayoutIssue",
    "AccessibilityIssue",
    "PerformanceMetric",
    "BrowserEvidence",
    "IssueSeverity",
    "IssueCategory",
    "Issue",
    "generate_stable_issue_id",
    "AuditStatus",
    "CreateAuditRequest",
    "AuditResult",
    "AuditComparison",
    "DeveloperFixPrompt",
]
