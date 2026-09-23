import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Set

from app.schemas.audit import (
    AuditResult,
    AuditStatus,
    AuditSummaryStats,
    AuditComparison,
    CreateAuditRequest,
)
from app.schemas.evidence import BrowserEvidence, ViewportAuditResult
from app.schemas.issue import (
    Issue,
    IssueCategory,
    IssueSeverity,
    generate_stable_issue_id,
    generate_deterministic_issue_id,
)
from app.services.browser.interface import BaseBrowserRunner
from app.services.browser.playwright_runner import PlaywrightBrowserRunner
from app.services.ai.interface import BaseLLMProvider, StubLLMProvider, AINotConfiguredError, AIProviderError
from app.services.ai.openai_provider import OpenAILLMProvider
from app.schemas.ai import IssueAnalysisResponse, AIAnalysisDetails

logger = logging.getLogger("uiproof.service")



def create_deterministic_findings(evidence: BrowserEvidence) -> List[Issue]:
    """
    Derives deterministic, evidence-backed issues from Playwright browser traces across 8 core categories:
    1. Console Errors
    2. Network Failures
    3. Horizontal Overflow
    4. Broken Images
    5. Broken Links
    6. Missing Page Title
    7. Missing Meta Description
    8. Basic Accessibility Violations

    Contains NO AI predictions. Deduplicated per viewport. Guaranteed stable across audit re-runs.
    """
    findings: List[Issue] = []
    seen_ids: Set[str] = set()

    viewport_results: List[Tuple[str, Optional[ViewportAuditResult]]] = [
        ("Desktop", evidence.desktop),
        ("Mobile", evidence.mobile),
    ]

    for vp_name, vp_res in viewport_results:
        if not vp_res:
            continue

        page_meta = vp_res.page
        resp = vp_res.responsive
        dom_meta = vp_res.dom_metadata

        # 1. Page Load / Navigation Failure (CRITICAL)
        if not page_meta.page_load_success or (page_meta.http_status and page_meta.http_status >= 400):
            status_text = f"HTTP {page_meta.http_status}" if page_meta.http_status else "Navigation Timeout / Connection Failure"
            title = f"Page Load Failure ({vp_name})"
            issue_id = generate_deterministic_issue_id("PAGE-LOAD-FAIL", vp_name)
            if issue_id not in seen_ids:
                seen_ids.add(issue_id)
                findings.append(
                    Issue(
                        issue_id=issue_id,
                        category=IssueCategory.LAYOUT,
                        severity=IssueSeverity.CRITICAL,
                        title=title,
                        description=f"Target web application failed to load successfully on {vp_name} viewport. Details: {status_text}. Error: {page_meta.error_message or 'None'}",
                        selector="window",
                        viewport=vp_name,
                        evidence_references=[page_meta.final_url or page_meta.initial_url]
                    )
                )

        # 2. Console Errors (HIGH)
        for log in vp_res.console_errors:
            title = f"Console Error Detected ({vp_name})"
            selector = log.location or "window"
            issue_id = generate_deterministic_issue_id("CONSOLE-ERROR", vp_name, log.text)
            if issue_id not in seen_ids:
                seen_ids.add(issue_id)
                findings.append(
                    Issue(
                        issue_id=issue_id,
                        category=IssueCategory.CONSOLE_ERROR,
                        severity=IssueSeverity.HIGH,
                        title=title,
                        description=f"Uncaught browser console error on {vp_name}: {log.text}",
                        selector=selector,
                        viewport=vp_name,
                        evidence_references=[f"Location: {log.location}"] if log.location else []
                    )
                )

        # 3. Network Request Failures (HIGH)
        for net in vp_res.network_failures:
            title = f"Network Request Failed ({vp_name}): {net.method} {net.url[:50]}"
            selector = net.url
            issue_id = generate_deterministic_issue_id("NETWORK-FAILURE", vp_name, net.url)
            if issue_id not in seen_ids:
                seen_ids.add(issue_id)
                findings.append(
                    Issue(
                        issue_id=issue_id,
                        category=IssueCategory.NETWORK_FAILURE,
                        severity=IssueSeverity.HIGH,
                        title=title,
                        description=f"Network request failure recorded on {vp_name}: {net.error_text} for URL {net.url} (Method: {net.method}, Status: {net.status_code or 'N/A'})",
                        selector=selector,
                        viewport=vp_name,
                        evidence_references=[net.url]
                    )
                )

        # 4. Horizontal Overflow (HIGH for Mobile, MEDIUM for Desktop)
        if resp and resp.horizontal_overflow > 5:
            title = f"{vp_name} Horizontal Overflow"
            severity = IssueSeverity.HIGH if vp_name.lower() == "mobile" else IssueSeverity.MEDIUM
            issue_id = generate_deterministic_issue_id("OVERFLOW", vp_name)
            if issue_id not in seen_ids:
                seen_ids.add(issue_id)
                findings.append(
                    Issue(
                        issue_id=issue_id,
                        category=IssueCategory.RESPONSIVE,
                        severity=severity,
                        title=title,
                        description=(
                            f"Document scroll width ({resp.document_scroll_width}px) exceeds client width "
                            f"({resp.document_client_width}px) by {resp.horizontal_overflow}px on {vp_name}, causing horizontal scrolling."
                        ),
                        selector="body",
                        viewport=vp_name,
                        evidence_references=[f"Viewport: {resp.viewport_width}px, ScrollWidth: {resp.document_scroll_width}px, Overflow: {resp.horizontal_overflow}px"]
                    )
                )

        # 5. Broken Images (MEDIUM)
        for img in vp_res.broken_images:
            title = f"Broken Image Detected ({vp_name})"
            issue_id = generate_deterministic_issue_id("BROKEN-IMAGE", vp_name, img.src)
            if issue_id not in seen_ids:
                seen_ids.add(issue_id)
                findings.append(
                    Issue(
                        issue_id=issue_id,
                        category=IssueCategory.BROKEN_RESOURCE,
                        severity=IssueSeverity.MEDIUM,
                        title=title,
                        description=f"Image failed to render on {vp_name}. Source URL: {img.src}. Alt: '{img.alt or 'None'}'. Error: {img.error_reason}",
                        selector=img.selector or "img",
                        viewport=vp_name,
                        evidence_references=[img.src]
                    )
                )

        # 6. Broken Links (MEDIUM)
        for link in vp_res.broken_links:
            title = f"Broken Link Detected ({vp_name}): {link.href[:50]}"
            issue_id = generate_deterministic_issue_id("BROKEN-LINK", vp_name, link.href)
            if issue_id not in seen_ids:
                seen_ids.add(issue_id)
                findings.append(
                    Issue(
                        issue_id=issue_id,
                        category=IssueCategory.BROKEN_RESOURCE,
                        severity=IssueSeverity.MEDIUM,
                        title=title,
                        description=f"Hyperlink on {vp_name} returned non-success response: {link.error_reason}. Target Href: {link.href}. Link Text: '{link.text}'",
                        selector="a[href]",
                        viewport=vp_name,
                        evidence_references=[link.href]
                    )
                )

        # 7. Missing Page Title (MEDIUM)
        if dom_meta and not dom_meta.has_title:
            title = f"Missing Page Title ({vp_name})"
            issue_id = generate_deterministic_issue_id("MISSING-TITLE", vp_name)
            if issue_id not in seen_ids:
                seen_ids.add(issue_id)
                findings.append(
                    Issue(
                        issue_id=issue_id,
                        category=IssueCategory.SEO,
                        severity=IssueSeverity.MEDIUM,
                        title=title,
                        description=f"The HTML document on {vp_name} is missing a non-empty <title> tag, impacting SEO and usability.",
                        selector="head > title",
                        viewport=vp_name,
                        evidence_references=[f"Title value: '{dom_meta.title or ''}'"]
                    )
                )

        # 8. Missing Meta Description (LOW)
        if dom_meta and not dom_meta.has_meta_description:
            title = f"Missing Meta Description ({vp_name})"
            issue_id = generate_deterministic_issue_id("MISSING-META", vp_name)
            if issue_id not in seen_ids:
                seen_ids.add(issue_id)
                findings.append(
                    Issue(
                        issue_id=issue_id,
                        category=IssueCategory.SEO,
                        severity=IssueSeverity.LOW,
                        title=title,
                        description=f"The HTML document on {vp_name} is missing a <meta name='description'> tag, impacting search engine indexing snippets.",
                        selector="head > meta[name='description']",
                        viewport=vp_name,
                        evidence_references=[f"Meta description: '{dom_meta.meta_description or ''}'"]
                    )
                )

        # 9. Basic Accessibility Issues (MEDIUM)
        for a11y in vp_res.a11y_violations:
            title = f"Basic Accessibility Issue: {a11y.rule_id} ({vp_name})"
            issue_id = generate_deterministic_issue_id(f"A11Y-{a11y.rule_id}", vp_name, a11y.selector)
            if issue_id not in seen_ids:
                seen_ids.add(issue_id)
                findings.append(
                    Issue(
                        issue_id=issue_id,
                        category=IssueCategory.ACCESSIBILITY,
                        severity=IssueSeverity.MEDIUM,
                        title=title,
                        description=f"Basic accessibility check violation on {vp_name}: {a11y.description}",
                        selector=a11y.selector,
                        viewport=vp_name,
                        evidence_references=[a11y.html_snippet] if a11y.html_snippet else []
                    )
                )

    return findings


class AuditEngineService:
    """
    Core orchestrator that coordinates:
    1. Browser evidence collection via Playwright runner
    2. Deterministic findings generation
    3. Before/After audit comparison logic
    """

    def __init__(
        self,
        browser_runner: Optional[BaseBrowserRunner] = None,
        ai_provider: Optional[BaseLLMProvider] = None,
    ):
        self.browser_runner = browser_runner or PlaywrightBrowserRunner()
        self.ai_provider = ai_provider or OpenAILLMProvider()
        self._audits_db: Dict[str, AuditResult] = {}

    async def analyze_issue(self, audit_id: str, issue_id: str) -> IssueAnalysisResponse:
        audit = self.get_audit(audit_id)
        if not audit:
            raise KeyError(f"Audit with ID '{audit_id}' not found.")

        all_issues = audit.issues if audit.issues else (audit.findings or [])
        target_issue = next((i for i in all_issues if i.issue_id == issue_id), None)
        if not target_issue:
            raise KeyError(f"Issue with ID '{issue_id}' not found in audit '{audit_id}'.")

        analysis_details = await self.ai_provider.analyze_issue(target_issue, audit.evidence)

        # Enrich in-memory issue instance
        causes_str = "\n".join(f"- {c}" for c in analysis_details.likely_causes) if analysis_details.likely_causes else "N/A"
        target_issue.root_cause_analysis = f"{analysis_details.summary}\n\nLikely Causes:\n{causes_str}"
        target_issue.recommended_fix = analysis_details.fix_prompt

        return IssueAnalysisResponse(
            audit_id=audit_id,
            issue_id=issue_id,
            issue=target_issue,
            analysis=analysis_details
        )

    async def create_audit(self, request: CreateAuditRequest) -> AuditResult:
        audit_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)

        try:
            # 1. Collect objective deterministic browser evidence
            evidence = await self.browser_runner.collect_evidence(
                url=request.url,
                viewports=request.viewports,
                audit_id=audit_id
            )

            # 2. Derive deterministic findings directly from browser evidence
            deterministic_findings = create_deterministic_findings(evidence)

            # 3. AI enrichment (Stubbed for Milestone 4A)
            ai_enriched_issues = await self.ai_provider.analyze_evidence(evidence)

            # Combine deterministic findings + any AI enriched issues
            all_issues = deterministic_findings + ai_enriched_issues

            completed_at = datetime.now(timezone.utc)

            # 4. Calculate summary metrics
            stats = AuditSummaryStats(
                total_issues=len(all_issues),
                critical_count=sum(1 for i in all_issues if i.severity == IssueSeverity.CRITICAL or i.severity == "critical"),
                high_count=sum(1 for i in all_issues if i.severity == IssueSeverity.HIGH or i.severity == "high"),
                medium_count=sum(1 for i in all_issues if i.severity == IssueSeverity.MEDIUM or i.severity == "medium"),
                low_count=sum(1 for i in all_issues if i.severity == IssueSeverity.LOW or i.severity == "low"),
                info_count=sum(1 for i in all_issues if i.severity == IssueSeverity.INFO or i.severity == "info"),
                console_error_count=len(evidence.console_errors),
                network_failure_count=len(evidence.network_failures),
                layout_issue_count=sum(1 for i in all_issues if i.category in (IssueCategory.LAYOUT, IssueCategory.RESPONSIVE, "layout", "responsive")),
                accessibility_issue_count=sum(1 for i in all_issues if i.category == IssueCategory.ACCESSIBILITY or i.category == "accessibility")
            )

            audit_result = AuditResult(
                audit_id=audit_id,
                target_url=request.url,
                url=request.url,
                status=AuditStatus.COMPLETED,
                created_at=started_at,
                started_at=started_at,
                completed_at=completed_at,
                desktop=evidence.desktop,
                mobile=evidence.mobile,
                evidence=evidence,
                issues=all_issues,
                findings=all_issues,
                stats=stats,
            )

            self._audits_db[audit_id] = audit_result
            return audit_result

        except Exception as err:
            import traceback
            tb_str = traceback.format_exc()
            logger.error(f"Audit failure for ID {audit_id}:\n{tb_str}")
            err_msg = f"{type(err).__name__}: {str(err)}" if str(err) else f"{type(err).__name__}: {repr(err)}"
            print(f"[AUDIT_ENGINE_ERROR] {tb_str}")
            failed_at = datetime.now(timezone.utc)
            failed_result = AuditResult(
                audit_id=audit_id,
                target_url=request.url,
                url=request.url,
                status=AuditStatus.FAILED,
                created_at=started_at,
                started_at=started_at,
                completed_at=failed_at,
                error_message=err_msg,
                issues=[],
                findings=[],
                stats=AuditSummaryStats()
            )
            self._audits_db[audit_id] = failed_result
            return failed_result

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
