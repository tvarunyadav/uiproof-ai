from abc import ABC, abstractmethod
from typing import List
from datetime import datetime, timezone
from app.schemas.evidence import BrowserEvidence, BrowserViewport


class BaseBrowserRunner(ABC):
    """
    Abstract interface for browser automation testing.
    Keeps Playwright implementation strictly isolated from API controllers and AI logic.
    """

    @abstractmethod
    async def collect_evidence(self, url: str, viewports: List[str]) -> BrowserEvidence:
        """Collect objective deterministic evidence from the target URL."""
        pass


class PlaywrightBrowserRunnerStub(BaseBrowserRunner):
    """
    Milestone 1 Browser Automation Interface Stub.
    Returns clean structural schema container. Real Playwright execution will be integrated in future milestone.
    """

    async def collect_evidence(self, url: str, viewports: List[str]) -> BrowserEvidence:
        parsed_viewports = [
            BrowserViewport(name="Desktop", width=1920, height=1080, device_scale_factor=1.0)
            if v == "desktop" else
            BrowserViewport(name="Mobile", width=375, height=812, device_scale_factor=2.0)
            for v in viewports
        ]

        return BrowserEvidence(
            url=url,
            timestamp=datetime.now(timezone.utc),
            viewports_tested=parsed_viewports,
            screenshot_paths=[],
            console_errors=[],
            network_failures=[],
            layout_issues=[],
            accessibility_issues=[],
            performance_metrics=[]
        )
