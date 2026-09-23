from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.issue import Issue


class IssueAnalysisRequest(BaseModel):
    prompt_format: Optional[str] = Field(default="standard", description="Format style e.g. standard, cursor, antigravity")


class AIAnalysisDetails(BaseModel):
    summary: str = Field(..., description="High-level summary of detected issue and root cause diagnosis")
    likely_causes: List[str] = Field(default=[], description="Observed evidence-grounded hypotheses of potential root causes")
    investigation_hints: List[str] = Field(default=[], description="Targeted debugging & inspection recommendations")
    expected_result: str = Field(..., description="Expected correct behavior once issue is resolved")
    constraints: List[str] = Field(default=[], description="Technical or layout constraints (e.g. preserve desktop responsiveness)")
    verification_steps: List[str] = Field(default=[], description="Measurable verification steps for testing the fix")
    fix_prompt: str = Field(..., description="Context-rich prompt formatted for developer AI coding tools")


class IssueAnalysisResponse(BaseModel):
    audit_id: str = Field(..., description="Parent Audit UUID")
    issue_id: str = Field(..., description="Deterministic stable Issue ID")
    issue: Issue = Field(..., description="Verified deterministic issue enriched with root_cause_analysis and recommended_fix")
    analysis: AIAnalysisDetails = Field(..., description="Structured AI analysis payload")
