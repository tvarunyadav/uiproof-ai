from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
from app.schemas.evidence import BrowserEvidence
from app.schemas.issue import Issue


class AuditStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CreateAuditRequest(BaseModel):
    url: str = Field(..., description="Target web application URL to audit")
    viewports: List[str] = Field(
        default=["desktop", "mobile"],
        description="Viewport sizes to test: desktop (1920x1080), mobile (375x812), tablet (768x1024)"
    )
    baseline_audit_id: Optional[str] = Field(
        None,
        description="Optional baseline audit ID for before/after fix verification comparison"
    )


class AuditSummaryStats(BaseModel):
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    console_error_count: int = 0
    network_failure_count: int = 0
    layout_issue_count: int = 0
    accessibility_issue_count: int = 0


class AuditResult(BaseModel):
    audit_id: str = Field(..., description="Unique UUID for this audit run")
    url: str
    status: AuditStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    evidence: Optional[BrowserEvidence] = None
    issues: List[Issue] = []
    stats: AuditSummaryStats = Field(default_factory=AuditSummaryStats)
    error_message: Optional[str] = None


class AuditComparison(BaseModel):
    baseline_audit_id: str
    new_audit_id: str
    created_at: datetime
    fixed_issues: List[Issue] = Field(default=[], description="Issues resolved in new audit")
    remaining_issues: List[Issue] = Field(default=[], description="Issues still present in new audit")
    new_issues: List[Issue] = Field(default=[], description="New issues introduced in new audit")
    regressions: List[Issue] = Field(default=[], description="Reintroduced or worsened issues")


class DeveloperFixPrompt(BaseModel):
    audit_id: str
    target_issues: List[Issue]
    fix_prompt: str = Field(..., description="Context-rich prompt formatted for Antigravity, Cursor, Claude, or VS Code")
    suggested_files: List[str] = []
