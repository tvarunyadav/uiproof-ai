from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.audit import AuditStatus


class CreateProjectRequest(BaseModel):
    name: str = Field(..., description="Project display name")
    target_url: str = Field(..., description="Target web application base URL")


class Project(BaseModel):
    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project display name")
    target_url: str = Field(..., description="Target web application base URL")
    created_at: datetime = Field(..., description="Project creation timestamp")
    audit_count: int = Field(default=0, description="Total number of audits run for this project")


class AuditSummaryItem(BaseModel):
    audit_id: str = Field(..., description="Audit UUID")
    project_id: Optional[str] = Field(None, description="Associated Project ID")
    target_url: str = Field(..., description="Target web application URL")
    mode: str = Field(default="remote", description="Audit execution mode: 'remote' or 'local'")
    status: AuditStatus = Field(..., description="Audit execution status")
    created_at: datetime = Field(..., description="Audit start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Audit completion timestamp")
    total_issues: int = Field(default=0, description="Total issues detected")
    critical_count: int = Field(default=0, description="Critical severity issue count")
    high_count: int = Field(default=0, description="High severity issue count")
    baseline_audit_id: Optional[str] = Field(None, description="Baseline audit ID if retest")
