import pytest
from pathlib import Path
from app.services.browser.playwright_runner import PlaywrightBrowserRunner


@pytest.mark.asyncio
async def test_playwright_runner_smoke_test(tmp_path):
    runner = PlaywrightBrowserRunner(artifacts_base_dir=tmp_path, timeout_ms=10000)

    # Use a data URL for fast, isolated, deterministic offline Playwright testing
    data_url = (
        "data:text/html;charset=utf-8,"
        "<html><head><title>UIProof Smoke Test</title></head>"
        "<body><h1 style='width: 2000px;'>Wide Content</h1></body></html>"
    )

    evidence = await runner.collect_evidence(
        url=data_url,
        viewports=["desktop", "mobile"],
        audit_id="smoke-test-audit"
    )

    assert evidence is not None
    assert evidence.desktop is not None
    assert evidence.mobile is not None
    assert evidence.desktop.page.title == "UIProof Smoke Test"
    assert evidence.desktop.page.page_load_success is True
    assert evidence.desktop.screenshot_artifact_id == "desktop.png"
    assert (tmp_path / "smoke-test-audit" / "desktop.png").exists()

    # Desktop width 1440, content width 2000 => overflow ~ 560px
    assert evidence.desktop.responsive.horizontal_overflow > 0
