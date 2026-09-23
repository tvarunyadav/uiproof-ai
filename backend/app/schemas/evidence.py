from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime


class BrowserViewport(BaseModel):
    name: str = Field(..., description="Viewport descriptor, e.g. Desktop, Mobile, Tablet")
    width: int = Field(..., description="Viewport width in pixels")
    height: int = Field(..., description="Viewport height in pixels")
    device_scale_factor: float = Field(default=1.0, description="DPI scale factor")


class ConsoleLogEntry(BaseModel):
    timestamp: datetime
    level: str = Field(..., description="Log level: error, warning, info, debug")
    text: str = Field(..., description="Console message content")
    location: Optional[str] = Field(None, description="Source script URL and line number")


class NetworkFailure(BaseModel):
    timestamp: datetime
    url: str = Field(..., description="Target request URL")
    method: str = Field(..., description="HTTP method e.g. GET, POST")
    status_code: Optional[int] = Field(None, description="HTTP status code if response received")
    error_text: str = Field(..., description="Failure message, e.g. net::ERR_CONNECTION_REFUSED")


class LayoutIssue(BaseModel):
    viewport: BrowserViewport
    selector: str = Field(..., description="CSS Selector of affected element")
    issue_type: str = Field(..., description="Category e.g. overflow, element_overlap, text_clipping")
    description: str = Field(..., description="Deterministic measurement breakdown")
    bounding_box: Optional[dict] = Field(None, description="x, y, width, height bounding box")


class AccessibilityIssue(BaseModel):
    rule_id: str = Field(..., description="WCAG or Axe rule identifier e.g. color-contrast, image-alt")
    impact: str = Field(..., description="Impact level: critical, serious, moderate, minor")
    selector: str = Field(..., description="CSS Selector of violating element")
    help_url: Optional[str] = Field(None, description="Reference link for remediation")
    description: str = Field(..., description="A11y violation summary")


class PerformanceMetric(BaseModel):
    metric_name: str = Field(..., description="e.g. LCP, FCP, CLS, TTFB, DOMContentLoaded")
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="ms, seconds, score")
    rating: str = Field(..., description="good, needs_improvement, poor")


class ResponsiveMetrics(BaseModel):
    viewport_width: int = Field(..., description="Configured viewport width in pixels")
    viewport_height: int = Field(..., description="Configured viewport height in pixels")
    document_scroll_width: int = Field(..., description="Measured document scroll width in pixels")
    document_client_width: int = Field(..., description="Measured document client width in pixels")
    horizontal_overflow: int = Field(..., description="Measured horizontal overflow pixels (scrollWidth - viewportWidth)")


class PageMetadata(BaseModel):
    initial_url: str = Field(..., description="Requested target URL")
    final_url: str = Field(..., description="Final URL after redirects")
    title: str = Field(..., description="Page document title")
    http_status: Optional[int] = Field(None, description="Main document HTTP response status code")
    page_load_success: bool = Field(True, description="Whether page load completed without critical failure")
    error_message: Optional[str] = Field(None, description="Navigation or load error detail if failed")


class BrokenImageEvidence(BaseModel):
    src: str = Field(..., description="Target image URL or src attribute")
    alt: Optional[str] = Field(None, description="Image alt attribute if provided")
    selector: Optional[str] = Field(None, description="DOM CSS selector if available")
    error_reason: str = Field(..., description="Failure details, e.g. naturalWidth is 0")


class BrokenLinkEvidence(BaseModel):
    href: str = Field(..., description="Target link URL")
    text: str = Field(..., description="Link anchor text content")
    status_code: Optional[int] = Field(None, description="HTTP status code if response received")
    error_reason: str = Field(..., description="Failure details, e.g. HTTP 404 or connection error")


class DOMMetadataEvidence(BaseModel):
    title: Optional[str] = Field(None, description="Document page title")
    has_title: bool = Field(False, description="Whether document has non-empty title")
    meta_description: Optional[str] = Field(None, description="Content of meta name='description'")
    has_meta_description: bool = Field(False, description="Whether document has non-empty meta description")


class AccessibilityViolation(BaseModel):
    rule_id: str = Field(..., description="Deterministic rule identifier e.g. missing-alt, unlabeled-input, empty-button")
    impact: str = Field("medium", description="Severity impact: critical, high, medium, low")
    selector: str = Field(..., description="CSS selector of element with violation")
    description: str = Field(..., description="Basic accessibility check summary")
    html_snippet: Optional[str] = Field(None, description="Outer HTML snippet if available")


class ViewportAuditResult(BaseModel):
    viewport: BrowserViewport
    page: PageMetadata
    screenshot_artifact_id: Optional[str] = Field(None, description="Identifier for full-page screenshot artifact")
    screenshot_url: Optional[str] = Field(None, description="Relative API URL to retrieve screenshot image")
    console_errors: List[ConsoleLogEntry] = Field(default=[], description="Errors captured from page console")
    console_logs: List[ConsoleLogEntry] = Field(default=[], description="All log messages captured from page console")
    network_failures: List[NetworkFailure] = Field(default=[], description="Failed network requests or 4xx/5xx responses")
    responsive: ResponsiveMetrics
    broken_images: List[BrokenImageEvidence] = Field(default=[], description="Images failing to render or load")
    broken_links: List[BrokenLinkEvidence] = Field(default=[], description="Broken hyperlinks returning HTTP 4xx/5xx or failed connection")
    dom_metadata: Optional[DOMMetadataEvidence] = Field(None, description="Page SEO & DOM header metadata state")
    a11y_violations: List[AccessibilityViolation] = Field(default=[], description="Deterministic basic accessibility violations")



class BrowserEvidence(BaseModel):
    """
    Deterministic objective test evidence collected directly by Playwright browser.
    This schema contains NO AI-generated analysis or predictions.
    """
    url: str
    timestamp: datetime
    desktop: Optional[ViewportAuditResult] = None
    mobile: Optional[ViewportAuditResult] = None
    viewports_tested: List[BrowserViewport] = []
    screenshot_paths: List[str] = []
    console_errors: List[ConsoleLogEntry] = []
    network_failures: List[NetworkFailure] = []
    layout_issues: List[LayoutIssue] = []
    accessibility_issues: List[AccessibilityIssue] = []
    performance_metrics: List[PerformanceMetric] = []

