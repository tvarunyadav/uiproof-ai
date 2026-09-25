import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Set

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, init_db
from app.db.models import ProjectModel, AuditModel, IssueModel, AIAnalysisModel
from app.schemas.ai import AIAnalysisDetails, IssueAnalysisResponse

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
    4. Database persistence for Audits and Issues
    """

    def __init__(
        self,
        browser_runner: Optional[BaseBrowserRunner] = None,
        ai_provider: Optional[BaseLLMProvider] = None,
    ):
        self.browser_runner = browser_runner or PlaywrightBrowserRunner()
        self.ai_provider = ai_provider or OpenAILLMProvider()
        self._audits_db: Dict[str, AuditResult] = {}
        try:
            init_db()
        except Exception as e:
            logger.warning(f"Could not auto-initialize database in AuditEngineService: {e}")

    def _save_audit_to_db(
        self,
        audit_result: AuditResult,
        baseline_audit_id: Optional[str] = None,
        project_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> None:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            audit_model = db.query(AuditModel).filter_by(audit_id=audit_result.audit_id).first()
            status_str = audit_result.status.value if isinstance(audit_result.status, AuditStatus) else str(audit_result.status)
            stats_dict = audit_result.stats.model_dump() if audit_result.stats else {}
            evidence_dict = audit_result.evidence.model_dump(mode="json") if audit_result.evidence else None

            if not audit_model:
                audit_model = AuditModel(
                    audit_id=audit_result.audit_id,
                    project_id=project_id,
                    target_url=audit_result.target_url or audit_result.url,
                    baseline_audit_id=baseline_audit_id,
                    status=status_str,
                    created_at=audit_result.created_at or datetime.now(timezone.utc),
                    started_at=audit_result.started_at,
                    completed_at=audit_result.completed_at,
                    stats=stats_dict,
                    evidence=evidence_dict,
                    error_message=audit_result.error_message,
                )
                db.add(audit_model)
            else:
                audit_model.target_url = audit_result.target_url or audit_result.url
                audit_model.status = status_str
                if baseline_audit_id:
                    audit_model.baseline_audit_id = baseline_audit_id
                if project_id:
                    audit_model.project_id = project_id
                audit_model.completed_at = audit_result.completed_at
                audit_model.stats = stats_dict
                audit_model.evidence = evidence_dict
                audit_model.error_message = audit_result.error_message

            all_issues = audit_result.issues if audit_result.issues else (audit_result.findings or [])
            for issue in all_issues:
                cat_val = issue.category.value if isinstance(issue.category, IssueCategory) else str(issue.category)
                sev_val = issue.severity.value if isinstance(issue.severity, IssueSeverity) else str(issue.severity)

                existing_issue = db.query(IssueModel).filter_by(audit_id=audit_result.audit_id, issue_id=issue.issue_id).first()
                if not existing_issue:
                    issue_model = IssueModel(
                        issue_id=issue.issue_id,
                        audit_id=audit_result.audit_id,
                        category=cat_val,
                        severity=sev_val,
                        title=issue.title,
                        description=issue.description,
                        selector=issue.selector,
                        viewport=issue.viewport,
                        evidence_references=issue.evidence_references or [],
                        root_cause_analysis=issue.root_cause_analysis,
                        recommended_fix=issue.recommended_fix,
                    )
                    db.add(issue_model)
                else:
                    existing_issue.root_cause_analysis = issue.root_cause_analysis
                    existing_issue.recommended_fix = issue.recommended_fix
                    existing_issue.evidence_references = issue.evidence_references or []

            db.commit()
            self._audits_db[audit_result.audit_id] = audit_result
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving audit {audit_result.audit_id} to DB: {e}")
            raise e
        finally:
            if close_db:
                db.close()

    def get_audit(self, audit_id: str, user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[AuditResult]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            audit_model = db.query(AuditModel).filter_by(audit_id=audit_id).first()
            if audit_model:
                # Ownership check: If audit belongs to a project owned by another user, return None (404)
                if audit_model.project_id and user_id:
                    proj = db.query(ProjectModel).filter_by(project_id=audit_model.project_id).first()
                    if proj and proj.user_id and proj.user_id != user_id:
                        return None

                issues = []
                for i in audit_model.issues:
                    cat = IssueCategory(i.category) if i.category in IssueCategory._value2member_map_ else i.category
                    sev = IssueSeverity(i.severity) if i.severity in IssueSeverity._value2member_map_ else i.severity
                    issues.append(
                        Issue(
                            issue_id=i.issue_id,
                            category=cat,
                            severity=sev,
                            title=i.title,
                            description=i.description,
                            selector=i.selector,
                            viewport=i.viewport,
                            evidence_references=i.evidence_references or [],
                            root_cause_analysis=i.root_cause_analysis,
                            recommended_fix=i.recommended_fix,
                        )
                    )

                evidence_obj = None
                if audit_model.evidence:
                    try:
                        evidence_obj = BrowserEvidence.model_validate(audit_model.evidence)
                    except Exception as e:
                        logger.warning(f"Failed to deserialize evidence for audit {audit_id}: {e}")
                        evidence_obj = None

                stats_obj = AuditSummaryStats()
                if audit_model.stats:
                    try:
                        stats_obj = AuditSummaryStats.model_validate(audit_model.stats)
                    except Exception as e:
                        logger.warning(f"Failed to deserialize stats for audit {audit_id}: {e}")

                status_enum = AuditStatus(audit_model.status) if audit_model.status in AuditStatus._value2member_map_ else audit_model.status

                created_at = audit_model.created_at
                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                started_at = audit_model.started_at
                if started_at and started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)

                completed_at = audit_model.completed_at
                if completed_at and completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=timezone.utc)

                result = AuditResult(
                    audit_id=audit_model.audit_id,
                    target_url=audit_model.target_url,
                    url=audit_model.target_url,
                    status=status_enum,
                    created_at=created_at,
                    started_at=started_at,
                    completed_at=completed_at,
                    desktop=evidence_obj.desktop if evidence_obj else None,
                    mobile=evidence_obj.mobile if evidence_obj else None,
                    evidence=evidence_obj,
                    issues=issues,
                    findings=issues,
                    stats=stats_obj,
                    error_message=audit_model.error_message,
                )
                self._audits_db[audit_id] = result
                return result

            return self._audits_db.get(audit_id)
        except Exception as e:
            logger.error(f"Error querying audit {audit_id} from DB: {e}")
            return self._audits_db.get(audit_id)
        finally:
            if close_db:
                db.close()

    def get_ai_analysis(self, audit_id: str, issue_id: str, user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[AIAnalysisDetails]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            if user_id:
                audit = self.get_audit(audit_id, user_id=user_id, db=db)
                if not audit:
                    return None

            analysis_model = (
                db.query(AIAnalysisModel)
                .filter_by(audit_id=audit_id, issue_id=issue_id)
                .order_by(AIAnalysisModel.created_at.desc())
                .first()
            )
            if analysis_model:
                return AIAnalysisDetails(
                    summary=analysis_model.summary,
                    likely_causes=analysis_model.likely_causes or [],
                    investigation_hints=analysis_model.investigation_hints or [],
                    expected_result=analysis_model.expected_result,
                    constraints=analysis_model.constraints or [],
                    verification_steps=analysis_model.verification_steps or [],
                    fix_prompt=analysis_model.fix_prompt,
                )
            return None
        except Exception as e:
            logger.warning(f"Error querying AIAnalysisModel for audit {audit_id}, issue {issue_id}: {e}")
            return None
        finally:
            if close_db:
                db.close()

    async def analyze_issue(self, audit_id: str, issue_id: str, user_id: Optional[str] = None, db: Optional[Session] = None) -> IssueAnalysisResponse:
        audit = self.get_audit(audit_id, user_id=user_id, db=db)
        if not audit:
            raise KeyError(f"Audit with ID '{audit_id}' not found.")

        all_issues = audit.issues if audit.issues else (audit.findings or [])
        target_issue = next((i for i in all_issues if i.issue_id == issue_id), None)
        if not target_issue:
            raise KeyError(f"Issue with ID '{issue_id}' not found in audit '{audit_id}'.")

        # 1. Check if AI analysis is already persisted in the database
        existing_analysis = self.get_ai_analysis(audit_id=audit_id, issue_id=issue_id, user_id=user_id, db=db)
        if existing_analysis:
            causes_str = "\n".join(f"- {c}" for c in existing_analysis.likely_causes) if existing_analysis.likely_causes else "N/A"
            target_issue.root_cause_analysis = f"{existing_analysis.summary}\n\nLikely Causes:\n{causes_str}"
            target_issue.recommended_fix = existing_analysis.fix_prompt

            return IssueAnalysisResponse(
                audit_id=audit_id,
                issue_id=issue_id,
                issue=target_issue,
                analysis=existing_analysis
            )

        # 2. If not persisted, invoke AI provider
        analysis_details = await self.ai_provider.analyze_issue(target_issue, audit.evidence)

        # Enrich target issue instance
        causes_str = "\n".join(f"- {c}" for c in analysis_details.likely_causes) if analysis_details.likely_causes else "N/A"
        target_issue.root_cause_analysis = f"{analysis_details.summary}\n\nLikely Causes:\n{causes_str}"
        target_issue.recommended_fix = analysis_details.fix_prompt

        # 3. Persist AIAnalysisModel and update IssueModel
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            ai_model = AIAnalysisModel(
                audit_id=audit_id,
                issue_id=issue_id,
                summary=analysis_details.summary,
                likely_causes=analysis_details.likely_causes or [],
                investigation_hints=analysis_details.investigation_hints or [],
                expected_result=analysis_details.expected_result,
                constraints=analysis_details.constraints or [],
                verification_steps=analysis_details.verification_steps or [],
                fix_prompt=analysis_details.fix_prompt,
            )
            db.add(ai_model)

            issue_model = db.query(IssueModel).filter_by(audit_id=audit_id, issue_id=issue_id).first()
            if issue_model:
                issue_model.root_cause_analysis = target_issue.root_cause_analysis
                issue_model.recommended_fix = target_issue.recommended_fix

            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not persist AI analysis record to DB: {e}")
        finally:
            if close_db:
                db.close()

        return IssueAnalysisResponse(
            audit_id=audit_id,
            issue_id=issue_id,
            issue=target_issue,
            analysis=analysis_details
        )

    async def create_audit(self, request: CreateAuditRequest, user_id: Optional[str] = None, db: Optional[Session] = None) -> AuditResult:
        # Verify target project ownership if project_id is specified
        if request.project_id:
            from app.services.project import project_service
            proj = project_service.get_project(request.project_id, user_id=user_id, db=db)
            if not proj:
                raise KeyError(f"Project with ID '{request.project_id}' not found.")

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

            self._save_audit_to_db(
                audit_result,
                baseline_audit_id=request.baseline_audit_id,
                project_id=request.project_id,
                db=db
            )
            return audit_result

        except Exception as err:
            if isinstance(err, KeyError):
                raise err
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
            self._save_audit_to_db(
                failed_result,
                baseline_audit_id=request.baseline_audit_id,
                project_id=request.project_id,
                db=db
            )
            return failed_result

    async def retest_audit(self, audit_id: str, user_id: Optional[str] = None, db: Optional[Session] = None) -> Tuple[AuditResult, AuditComparison]:
        baseline = self.get_audit(audit_id, user_id=user_id, db=db)
        if not baseline:
            raise KeyError(f"Baseline audit with ID '{audit_id}' not found.")

        # Determine baseline project_id if present
        baseline_project_id = None
        close_db = False
        db_s = db
        if db_s is None:
            db_s = SessionLocal()
            close_db = True
        try:
            baseline_model = db_s.query(AuditModel).filter_by(audit_id=audit_id).first()
            if baseline_model and baseline_model.project_id:
                baseline_project_id = baseline_model.project_id
        finally:
            if close_db:
                db_s.close()

        # Preserve baseline audit's viewport configuration
        viewports: List[str] = []
        if baseline.desktop:
            viewports.append("desktop")
        if baseline.mobile:
            viewports.append("mobile")
        if not viewports:
            viewports = ["desktop", "mobile"]

        target_url = baseline.target_url or baseline.url
        retest_request = CreateAuditRequest(
            url=target_url,
            viewports=viewports,
            baseline_audit_id=audit_id,
            project_id=baseline_project_id
        )

        retest_audit_result = await self.create_audit(retest_request, user_id=user_id, db=db)
        comparison = self.compare_audits(baseline_id=audit_id, new_id=retest_audit_result.audit_id, user_id=user_id, db=db)
        if not comparison:
            comparison = AuditComparison(
                baseline_audit_id=audit_id,
                new_audit_id=retest_audit_result.audit_id,
                created_at=datetime.now(timezone.utc),
                fixed_issues=[],
                remaining_issues=[],
                new_issues=[],
                regressions=[]
            )

        return retest_audit_result, comparison

    def compare_audits(self, baseline_id: str, new_id: str, user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[AuditComparison]:
        baseline = self.get_audit(baseline_id, user_id=user_id, db=db)
        new_audit = self.get_audit(new_id, user_id=user_id, db=db)

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

