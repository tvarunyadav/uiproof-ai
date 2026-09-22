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


class BrowserEvidence(BaseModel):
    """
    Deterministic objective test evidence collected directly by Playwright browser.
    This schema contains NO AI-generated analysis or predictions.
    """
    url: str
    timestamp: datetime
    viewports_tested: List[BrowserViewport] = []
    screenshot_paths: List[str] = []
    console_errors: List[ConsoleLogEntry] = []
    network_failures: List[NetworkFailure] = []
    layout_issues: List[LayoutIssue] = []
    accessibility_issues: List[AccessibilityIssue] = []
    performance_metrics: List[PerformanceMetric] = []
