import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.audit import (
    AuditResult,
    AuditStatus,
    AuditSummaryStats,
    AuditComparison,
    CreateAuditRequest,
)
from app.schemas.issue import Issue
from app.services.browser.interface import BaseBrowserRunner, PlaywrightBrowserRunnerStub
from app.services.ai.interface import BaseLLMProvider, StubLLMProvider


class AuditEngineService:
    """
    Core orchestrator that coordinates:
    1. Browser evidence collection (Playwright runner)
    2. Structured issue generation & AI enrichment
    3. Before/After audit comparison logic
    """

    def __init__(
        self,
        browser_runner: Optional[BaseBrowserRunner] = None,
        ai_provider: Optional[BaseLLMProvider] = None,
    ):
        self.browser_runner = browser_runner or PlaywrightBrowserRunnerStub()
        self.ai_provider = ai_provider or StubLLMProvider()
        # In-memory storage stub for Milestone 1 (prepared for PostgreSQL persistence)
        self._audits_db: Dict[str, AuditResult] = {}

    async def create_audit(self, request: CreateAuditRequest) -> AuditResult:
        audit_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # 1. Collect objective deterministic browser evidence
        evidence = await self.browser_runner.collect_evidence(
            url=request.url,
            viewports=request.viewports
        )

        # 2. Analyze evidence and produce structured issues
        issues = await self.ai_provider.analyze_evidence(evidence)

        # 3. Calculate summary metrics
        stats = AuditSummaryStats(
            total_issues=len(issues),
            critical_count=sum(1 for i in issues if i.severity == "critical"),
            high_count=sum(1 for i in issues if i.severity == "high"),
            medium_count=sum(1 for i in issues if i.severity == "medium"),
            low_count=sum(1 for i in issues if i.severity == "low"),
            info_count=sum(1 for i in issues if i.severity == "info"),
        )

        audit_result = AuditResult(
            audit_id=audit_id,
            url=request.url,
            status=AuditStatus.COMPLETED,
            created_at=now,
            completed_at=now,
            evidence=evidence,
            issues=issues,
            stats=stats,
        )

        self._audits_db[audit_id] = audit_result
        return audit_result

    def get_audit(self, audit_id: str) -> Optional[AuditResult]:
        return self._audits_db.get(audit_id)

    def compare_audits(self, baseline_id: str, new_id: str) -> Optional[AuditComparison]:
        baseline = self._audits_db.get(baseline_id)
        new_audit = self._audits_db.get(new_id)

        if not baseline or not new_audit:
            return None

        baseline_issue_map = {i.issue_id: i for i in baseline.issues}
        new_issue_map = {i.issue_id: i for i in new_audit.issues}

        fixed_issues = [i for i_id, i in baseline_issue_map.items() if i_id not in new_issue_map]
        remaining_issues = [i for i_id, i in new_issue_map.items() if i_id in baseline_issue_map]
        new_issues = [i for i_id, i in new_issue_map.items() if i_id not in baseline_issue_map]

        return AuditComparison(
            baseline_audit_id=baseline_id,
            new_audit_id=new_id,
            created_at=datetime.now(timezone.utc),
            fixed_issues=fixed_issues,
            remaining_issues=remaining_issues,
            new_issues=new_issues,
            regressions=[]
        )


# Global singleton instance for service injection
audit_engine = AuditEngineService()
