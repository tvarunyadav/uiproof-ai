import pytest
from pathlib import Path
from app.api.v1.endpoints.audits import ARTIFACTS_BASE_DIR


@pytest.mark.asyncio
async def test_artifact_path_traversal_rejection(async_client):
    response = await async_client.get("/api/v1/audits/../../etc/artifacts/desktop.png")
    # Should return 404 or 400 rejection
    assert response.status_code in (404, 400, 422)


@pytest.mark.asyncio
async def test_artifact_serving(async_client):
    test_audit_id = "test-audit-123"
    test_artifact_id = "desktop.png"

    audit_dir = ARTIFACTS_BASE_DIR / test_audit_id
    audit_dir.mkdir(parents=True, exist_ok=True)
    dummy_file = audit_dir / test_artifact_id
    dummy_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

    try:
        response = await async_client.get(f"/api/v1/audits/{test_audit_id}/artifacts/{test_artifact_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
    finally:
        if dummy_file.exists():
            dummy_file.unlink()
        if audit_dir.exists():
            audit_dir.rmdir()
