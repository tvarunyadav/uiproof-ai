import os
import sys
import uuid
import logging
import asyncio
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import httpx
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page, ConsoleMessage, Request, Response

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
from app.services.browser.interface import BaseBrowserRunner
from app.utils.security import validate_and_sanitize_url

from app.config import settings

logger = logging.getLogger("uiproof.browser")
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))


class PlaywrightBrowserRunner(BaseBrowserRunner):
    """
    Real Playwright Chromium Audit Runner.
    Runs desktop (1440x900) and mobile (390x844) viewport tests in isolated browser contexts.
    Uses an isolated worker thread loop to ensure 100% compatibility with Uvicorn and Windows ProactorEventLoop.
    """

    def __init__(self, artifacts_base_dir: Optional[Path] = None, timeout_ms: int = 30000):
        self.artifacts_dir = artifacts_base_dir or settings.artifacts_path
        self.timeout_ms = timeout_ms
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    async def collect_evidence(
        self,
        url: str,
        viewports: List[str],
        audit_id: Optional[str] = None
    ) -> BrowserEvidence:
        current_audit_id = audit_id or str(uuid.uuid4())
        
        # Execute Playwright in dedicated worker thread to guarantee ProactorEventLoop on Windows
        return await asyncio.to_thread(
            self._run_in_worker_thread,
            url,
            viewports,
            current_audit_id
        )

    def _run_in_worker_thread(self, url: str, viewports: List[str], audit_id: str) -> BrowserEvidence:
        if sys.platform == "win32":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception as loop_policy_err:
                logger.warning(f"Could not set WindowsProactorEventLoopPolicy: {loop_policy_err}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._collect_evidence_async(url, viewports, audit_id)
            )
        finally:
            try:
                loop.close()
            except Exception:
                pass

    async def _collect_evidence_async(
        self,
        url: str,
        viewports: List[str],
        audit_id: str
    ) -> BrowserEvidence:
        logger.info(f"[AUDIT_START] Audit ID: {audit_id} | Target URL: {url} | Viewports: {viewports}")
        audit_artifact_dir = self.artifacts_dir / audit_id
        audit_artifact_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        
        desktop_result: Optional[ViewportAuditResult] = None
        mobile_result: Optional[ViewportAuditResult] = None
        viewports_tested: List[BrowserViewport] = []
        all_screenshot_paths: List[str] = []
        all_console_errors: List[ConsoleLogEntry] = []
        all_network_failures: List[NetworkFailure] = []

        browser: Optional[Browser] = None
        
        async with async_playwright() as p:
            try:
                logger.info("[BROWSER_LAUNCH] Launching Playwright Chromium headless...")
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
                logger.info("[BROWSER_LAUNCH_SUCCESS] Chromium launched successfully.")

                # 1. Desktop Audit (1440 x 900) if requested
                if "desktop" in viewports or not viewports:
                    vp_config = BrowserViewport(
                        name="Desktop",
                        width=1440,
                        height=900,
                        device_scale_factor=1.0
                    )
                    logger.info(f"[DESKTOP_START] Starting Desktop audit ({vp_config.width}x{vp_config.height})...")
                    desktop_result = await self._audit_viewport(
                        browser=browser,
                        url=url,
                        audit_id=audit_id,
                        viewport=vp_config,
                        audit_dir=audit_artifact_dir,
                        is_mobile=False
                    )
                    viewports_tested.append(vp_config)
                    if desktop_result.screenshot_artifact_id:
                        all_screenshot_paths.append(desktop_result.screenshot_artifact_id)
                    all_console_errors.extend(desktop_result.console_errors)
                    all_network_failures.extend(desktop_result.network_failures)
                    logger.info(
                        f"[DESKTOP_COMPLETE] Title='{desktop_result.page.title}' | Status={desktop_result.page.http_status} | "
                        f"ConsoleErrors={len(desktop_result.console_errors)} | NetworkFailures={len(desktop_result.network_failures)} | "
                        f"Overflow={desktop_result.responsive.horizontal_overflow}px | BrokenImages={len(desktop_result.broken_images)} | "
                        f"BrokenLinks={len(desktop_result.broken_links)}"
                    )

                # 2. Mobile Audit (390 x 844) if requested
                if "mobile" in viewports or not viewports:
                    vp_config = BrowserViewport(
                        name="Mobile",
                        width=390,
                        height=844,
                        device_scale_factor=2.0
                    )
                    logger.info(f"[MOBILE_START] Starting Mobile audit ({vp_config.width}x{vp_config.height})...")
                    mobile_result = await self._audit_viewport(
                        browser=browser,
                        url=url,
                        audit_id=audit_id,
                        viewport=vp_config,
                        audit_dir=audit_artifact_dir,
                        is_mobile=True
                    )
                    viewports_tested.append(vp_config)
                    if mobile_result.screenshot_artifact_id:
                        all_screenshot_paths.append(mobile_result.screenshot_artifact_id)
                    all_console_errors.extend(mobile_result.console_errors)
                    all_network_failures.extend(mobile_result.network_failures)
                    logger.info(
                        f"[MOBILE_COMPLETE] Title='{mobile_result.page.title}' | Status={mobile_result.page.http_status} | "
                        f"ConsoleErrors={len(mobile_result.console_errors)} | NetworkFailures={len(mobile_result.network_failures)} | "
                        f"Overflow={mobile_result.responsive.horizontal_overflow}px | BrokenImages={len(mobile_result.broken_images)} | "
                        f"BrokenLinks={len(mobile_result.broken_links)}"
                    )

            except Exception as exc:
                tb = traceback.format_exc()
                logger.error(f"[AUDIT_FAILED] Error during Playwright execution for {url}:\n{tb}")
                raise RuntimeError(f"Playwright browser execution failed ({type(exc).__name__}): {exc or repr(exc)}") from exc
            finally:
                if browser:
                    logger.info("[BROWSER_CLOSE] Closing Chromium browser instance...")
                    try:
                        await browser.close()
                        logger.info("[BROWSER_CLOSE_SUCCESS] Browser closed cleanly.")
                    except Exception as close_err:
                        logger.warning(f"[BROWSER_CLOSE_ERROR] Error closing browser: {close_err}")

        logger.info(f"[AUDIT_SUCCESS] Completed Playwright audit for {url}")
        return BrowserEvidence(
            url=url,
            timestamp=now,
            desktop=desktop_result,
            mobile=mobile_result,
            viewports_tested=viewports_tested,
            screenshot_paths=all_screenshot_paths,
            console_errors=all_console_errors,
            network_failures=all_network_failures,
            layout_issues=[],
            accessibility_issues=[],
            performance_metrics=[]
        )

    async def _audit_viewport(
        self,
        browser: Browser,
        url: str,
        audit_id: str,
        viewport: BrowserViewport,
        audit_dir: Path,
        is_mobile: bool
    ) -> ViewportAuditResult:
        context: Optional[BrowserContext] = None
        
        console_logs: List[ConsoleLogEntry] = []
        console_errors: List[ConsoleLogEntry] = []
        network_failures: List[NetworkFailure] = []
        broken_images: List[BrokenImageEvidence] = []
        broken_links: List[BrokenLinkEvidence] = []
        dom_metadata: Optional[DOMMetadataEvidence] = None
        a11y_violations: List[AccessibilityViolation] = []

        initial_url = url
        final_url = url
        page_title = ""
        http_status: Optional[int] = None
        page_load_success = True
        error_message: Optional[str] = None
        screenshot_artifact_id: Optional[str] = None
        screenshot_url: Optional[str] = None

        viewport_name_lower = viewport.name.lower()

        try:
            logger.info(f"[{viewport.name}_CONTEXT_CREATE] Creating browser context...")
            context_opts: Dict[str, Any] = {
                "viewport": {"width": viewport.width, "height": viewport.height},
                "device_scale_factor": viewport.device_scale_factor,
                "is_mobile": is_mobile,
                "has_touch": is_mobile,
                "ignore_https_errors": True,
            }
            if is_mobile:
                context_opts["user_agent"] = (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
                )

            context = await browser.new_context(**context_opts)
            page = await context.new_page()

            # Register Console Listener
            def on_console(msg: ConsoleMessage):
                entry = ConsoleLogEntry(
                    timestamp=datetime.now(timezone.utc),
                    level=msg.type,
                    text=msg.text,
                    location=f"{msg.location.get('url', '')}:{msg.location.get('lineNumber', '')}"
                    if msg.location else None
                )
                console_logs.append(entry)
                if msg.type == "error":
                    console_errors.append(entry)
                    logger.warning(f"[{viewport.name}_CONSOLE_ERROR] {msg.text}")

            page.on("console", on_console)

            # Register Network Request Failure Listener
            def on_request_failed(req: Request):
                failure_text = req.failure if isinstance(req.failure, str) else (
                    req.failure.get("errorText") if isinstance(req.failure, dict) else "Request failed"
                )
                net_fail = NetworkFailure(
                    timestamp=datetime.now(timezone.utc),
                    url=req.url,
                    method=req.method,
                    status_code=None,
                    error_text=str(failure_text)
                )
                network_failures.append(net_fail)
                logger.warning(f"[{viewport.name}_NETWORK_FAILURE] {req.method} {req.url} -> {failure_text}")

            page.on("requestfailed", on_request_failed)

            # Register Response Status Listener (for 4xx/5xx HTTP responses)
            def on_response(res: Response):
                nonlocal http_status
                if res.url == page.url or res.url == url or res.url == initial_url or http_status is None:
                    http_status = res.status

                if res.status >= 400:
                    net_fail = NetworkFailure(
                        timestamp=datetime.now(timezone.utc),
                        url=res.url,
                        method=res.request.method,
                        status_code=res.status,
                        error_text=f"HTTP {res.status} {res.status_text}"
                    )
                    network_failures.append(net_fail)
                    logger.warning(f"[{viewport.name}_HTTP_ERROR] {res.status} {res.url}")

            page.on("response", on_response)

            # Navigate to page with timeout
            logger.info(f"[{viewport.name}_GOTO] Navigating to {url} (timeout={self.timeout_ms}ms)...")
            try:
                response = await page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
                if response:
                    http_status = response.status

                await asyncio.sleep(1)

                final_url = page.url
                try:
                    page_title = await page.title()
                except Exception:
                    page_title = final_url

                logger.info(f"[{viewport.name}_NAVIGATION_SUCCESS] Final URL: {final_url} | Title: '{page_title}' | Status: {http_status}")

            except Exception as nav_err:
                page_load_success = False
                raw_err = str(nav_err)
                if any(k in raw_err for k in ("ERR_CONNECTION_REFUSED", "connection refused", "failed to navigate", "ERR_NAME_NOT_RESOLVED")) and any(lh in url.lower() for lh in ("localhost", "127.0.0.1", "0.0.0.0")):
                    error_message = f"Unable to connect to the local website. Make sure the development server is running and accessible at {url}."
                else:
                    error_message = raw_err
                logger.warning(f"[{viewport.name}_NAVIGATION_FAIL] Error loading {url}: {error_message}")

            # Capture Full Page Screenshot
            try:
                artifact_filename = f"{viewport_name_lower}.png"
                screenshot_filepath = audit_dir / artifact_filename
                logger.info(f"[{viewport.name}_SCREENSHOT] Capturing full-page screenshot to {screenshot_filepath}...")
                await page.screenshot(path=str(screenshot_filepath), full_page=True)
                screenshot_artifact_id = artifact_filename
                screenshot_url = f"/api/v1/audits/{audit_id}/artifacts/{artifact_filename}"
                logger.info(f"[{viewport.name}_SCREENSHOT_SUCCESS] Screenshot saved: {artifact_filename}")
            except Exception as ss_err:
                logger.error(f"[{viewport.name}_SCREENSHOT_FAIL] Failed screenshot: {ss_err}")

            # Evaluate Responsive Metrics (Horizontal Overflow)
            logger.info(f"[{viewport.name}_EVALUATE_RESPONSIVE] Measuring DOM scrollWidth and clientWidth...")
            responsive_data = await self._evaluate_responsive_metrics(page, viewport)

            # Milestone 4A Extensions:
            # 1. Evaluate Broken Images
            logger.info(f"[{viewport.name}_EVALUATE_BROKEN_IMAGES] Inspecting <img> elements...")
            broken_images = await self._evaluate_broken_images(page)

            # 2. Evaluate DOM Metadata (Title & Meta Description)
            logger.info(f"[{viewport.name}_EVALUATE_METADATA] Inspecting <title> and <meta name='description'>...")
            dom_metadata = await self._evaluate_dom_metadata(page)

            # 3. Evaluate Basic Accessibility Violations
            logger.info(f"[{viewport.name}_EVALUATE_A11Y] Running basic deterministic accessibility checks...")
            a11y_violations = await self._evaluate_accessibility_violations(page)

            # 4. Evaluate Broken Links
            logger.info(f"[{viewport.name}_EVALUATE_BROKEN_LINKS] Verifying HTTP response of on-page links...")
            broken_links = await self._verify_on_page_links(page, final_url)

        except Exception as vp_err:
            page_load_success = False
            error_message = str(vp_err)
            logger.error(f"[{viewport.name}_AUDIT_ERROR] Viewport audit error: {vp_err}")
            responsive_data = ResponsiveMetrics(
                viewport_width=viewport.width,
                viewport_height=viewport.height,
                document_scroll_width=viewport.width,
                document_client_width=viewport.width,
                horizontal_overflow=0
            )
        finally:
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

        page_meta = PageMetadata(
            initial_url=initial_url,
            final_url=final_url,
            title=page_title or (final_url if final_url else initial_url),
            http_status=http_status,
            page_load_success=page_load_success,
            error_message=error_message
        )

        return ViewportAuditResult(
            viewport=viewport,
            page=page_meta,
            screenshot_artifact_id=screenshot_artifact_id,
            screenshot_url=screenshot_url,
            console_errors=console_errors,
            console_logs=console_logs,
            network_failures=network_failures,
            responsive=responsive_data,
            broken_images=broken_images,
            broken_links=broken_links,
            dom_metadata=dom_metadata,
            a11y_violations=a11y_violations
        )

    async def _evaluate_responsive_metrics(
        self,
        page: Page,
        viewport: BrowserViewport
    ) -> ResponsiveMetrics:
        try:
            dims = await page.evaluate("""
                () => {
                    const vw = window.innerWidth || document.documentElement.clientWidth || 0;
                    const vh = window.innerHeight || document.documentElement.clientHeight || 0;
                    const scrollWidth = Math.max(
                        document.documentElement.scrollWidth || 0,
                        document.body ? document.body.scrollWidth : 0
                    );
                    const clientWidth = Math.max(
                        document.documentElement.clientWidth || 0,
                        document.body ? document.body.clientWidth : 0
                    );
                    const overflow = Math.max(0, scrollWidth - vw);
                    return {
                        viewport_width: vw || """ + str(viewport.width) + """,
                        viewport_height: vh || """ + str(viewport.height) + """,
                        document_scroll_width: scrollWidth || vw || """ + str(viewport.width) + """,
                        document_client_width: clientWidth || vw || """ + str(viewport.width) + """,
                        horizontal_overflow: overflow
                    };
                }
            """)
            return ResponsiveMetrics(
                viewport_width=dims.get("viewport_width", viewport.width),
                viewport_height=dims.get("viewport_height", viewport.height),
                document_scroll_width=dims.get("document_scroll_width", viewport.width),
                document_client_width=dims.get("document_client_width", viewport.width),
                horizontal_overflow=dims.get("horizontal_overflow", 0)
            )
        except Exception as eval_err:
            logger.warning(f"[_evaluate_responsive_metrics] Failed to evaluate DOM dimensions: {eval_err}")
            return ResponsiveMetrics(
                viewport_width=viewport.width,
                viewport_height=viewport.height,
                document_scroll_width=viewport.width,
                document_client_width=viewport.width,
                horizontal_overflow=0
            )

    async def _evaluate_broken_images(self, page: Page) -> List[BrokenImageEvidence]:
        broken: List[BrokenImageEvidence] = []
        try:
            raw_imgs = await page.evaluate("""
                () => {
                    const imgs = Array.from(document.querySelectorAll('img'));
                    return imgs.map((img, idx) => {
                        const src = img.src || img.getAttribute('src') || '';
                        const alt = img.getAttribute('alt');
                        const isBroken = img.complete && (img.naturalWidth === 0 || img.naturalHeight === 0);
                        const sel = img.id ? `#${img.id}` : (img.className ? `img.${img.className.trim().replace(/\\s+/g, '.')}` : `img:nth-of-type(${idx + 1})`);
                        return {
                            src: src,
                            alt: alt,
                            selector: sel,
                            is_broken: isBroken
                        };
                    }).filter(i => i.src && i.is_broken);
                }
            """)
            for item in raw_imgs:
                broken.append(
                    BrokenImageEvidence(
                        src=item["src"],
                        alt=item.get("alt"),
                        selector=item.get("selector"),
                        error_reason="Image failed to render (naturalWidth === 0)"
                    )
                )
        except Exception as err:
            logger.warning(f"[_evaluate_broken_images] Failed to inspect images: {err}")
        return broken

    async def _evaluate_dom_metadata(self, page: Page) -> DOMMetadataEvidence:
        try:
            meta = await page.evaluate("""
                () => {
                    const titleEl = document.querySelector('title');
                    const title = titleEl ? (titleEl.textContent || '').trim() : '';
                    const metaDesc = document.querySelector('meta[name="description"]');
                    const desc = metaDesc ? (metaDesc.getAttribute('content') || '').trim() : '';
                    return {
                        title: title,
                        has_title: title.length > 0,
                        meta_description: desc,
                        has_meta_description: desc.length > 0
                    };
                }
            """)
            return DOMMetadataEvidence(
                title=meta.get("title") or None,
                has_title=bool(meta.get("has_title")),
                meta_description=meta.get("meta_description") or None,
                has_meta_description=bool(meta.get("has_meta_description"))
            )
        except Exception as err:
            logger.warning(f"[_evaluate_dom_metadata] Failed to inspect DOM metadata: {err}")
            return DOMMetadataEvidence(title=None, has_title=False, meta_description=None, has_meta_description=False)

    async def _evaluate_accessibility_violations(self, page: Page) -> List[AccessibilityViolation]:
        violations: List[AccessibilityViolation] = []
        try:
            raw_violations = await page.evaluate("""
                () => {
                    const items = [];
                    
                    // 1. Images missing alt
                    document.querySelectorAll('img:not([alt])').forEach((img, idx) => {
                        const sel = img.id ? `#${img.id}` : `img:nth-of-type(${idx + 1})`;
                        items.push({
                            rule_id: 'missing-alt',
                            impact: 'medium',
                            selector: sel,
                            description: 'Basic accessibility check: Image element is missing an alt attribute.',
                            html_snippet: img.outerHTML.slice(0, 150)
                        });
                    });

                    // 2. Unlabeled form input controls
                    document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"]):not([type="image"])').forEach((input, idx) => {
                        const hasAria = input.hasAttribute('aria-label') || input.hasAttribute('aria-labelledby');
                        const id = input.id;
                        const hasLabelTag = id ? !!document.querySelector(`label[for="${id}"]`) : false;
                        const isWrappedInLabel = !!input.closest('label');
                        if (!hasAria && !hasLabelTag && !isWrappedInLabel) {
                            const sel = id ? `#${id}` : (input.name ? `input[name="${input.name}"]` : `input:nth-of-type(${idx + 1})`);
                            items.push({
                                rule_id: 'unlabeled-form-control',
                                impact: 'medium',
                                selector: sel,
                                description: 'Basic accessibility check: Form input control has no associated <label> or aria-label attribute.',
                                html_snippet: input.outerHTML.slice(0, 150)
                            });
                        }
                    });

                    // 3. Empty buttons or links
                    document.querySelectorAll('button, a[href]').forEach((el, idx) => {
                        const text = (el.textContent || '').trim();
                        const hasAria = el.hasAttribute('aria-label') || el.hasAttribute('aria-labelledby') || el.hasAttribute('title');
                        const hasChildImg = !!el.querySelector('img[alt]:not([alt=""])');
                        if (!text && !hasAria && !hasChildImg) {
                            const tag = el.tagName.toLowerCase();
                            const sel = el.id ? `#${el.id}` : `${tag}:nth-of-type(${idx + 1})`;
                            items.push({
                                rule_id: 'empty-button-link',
                                impact: 'medium',
                                selector: sel,
                                description: `Basic accessibility check: ${tag === 'button' ? 'Button' : 'Link'} element contains no readable text or accessible label.`,
                                html_snippet: el.outerHTML.slice(0, 150)
                            });
                        }
                    });

                    return items;
                }
            """)
            for item in raw_violations:
                violations.append(
                    AccessibilityViolation(
                        rule_id=item["rule_id"],
                        impact=item.get("impact", "medium"),
                        selector=item["selector"],
                        description=item["description"],
                        html_snippet=item.get("html_snippet")
                    )
                )
        except Exception as err:
            logger.warning(f"[_evaluate_accessibility_violations] Failed to run a11y checks: {err}")
        return violations

    async def _verify_on_page_links(self, page: Page, base_url: str) -> List[BrokenLinkEvidence]:
        broken: List[BrokenLinkEvidence] = []
        try:
            raw_links = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.map(a => ({
                        href: a.href || a.getAttribute('href') || '',
                        text: (a.textContent || a.getAttribute('aria-label') || '').trim().slice(0, 80)
                    })).filter(l => l.href && (l.href.startsWith('http://') || l.href.startsWith('https://')));
                }
            """)

            # Deduplicate by href
            unique_links: Dict[str, str] = {}
            for item in raw_links:
                href = item["href"]
                if href not in unique_links:
                    unique_links[href] = item["text"]

            # Cap max checked links to 20 per audit to remain fast and bounded
            target_hrefs = list(unique_links.items())[:20]
            if not target_hrefs:
                return []

            async with httpx.AsyncClient(follow_redirects=True, timeout=3.0, verify=False) as client:
                for href, text in target_hrefs:
                    try:
                        validate_and_sanitize_url(href, allow_localhost=False)
                    except Exception:
                        # Skip localhost / internal IP links from external verification
                        continue

                    try:
                        res = await client.head(href)
                        if res.status_code == 405:
                            res = await client.get(href)

                        if res.status_code >= 400:
                            broken.append(
                                BrokenLinkEvidence(
                                    href=href,
                                    text=text or href,
                                    status_code=res.status_code,
                                    error_reason=f"HTTP {res.status_code}"
                                )
                            )
                    except Exception as req_err:
                        broken.append(
                            BrokenLinkEvidence(
                                href=href,
                                text=text or href,
                                status_code=None,
                                error_reason=f"Request failure: {type(req_err).__name__}"
                            )
                        )
        except Exception as err:
            logger.warning(f"[_verify_on_page_links] Link check error: {err}")
        return broken
