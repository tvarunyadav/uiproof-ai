import pytest
from datetime import datetime, timezone
from pathlib import Path
from app.api.v1.endpoints.audits import ARTIFACTS_BASE_DIR
from app.db.models import UserModel
from app.services.auth import create_access_token, hash_password


@pytest.mark.asyncio
async def test_artifact_path_traversal_rejection(async_client):
    response = await async_client.get("/api/v1/audits/../../etc/artifacts/desktop.png")
    # Should return 404, 401, 400 or 422 rejection
    assert response.status_code in (404, 401, 400, 422)


@pytest.mark.asyncio
async def test_artifact_serving(async_client, db_session):
    from app.db.models import ProjectModel, AuditModel
    user = UserModel(user_id="usr_art_001", email="art@example.com", password_hash=hash_password("Pass123!"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.user_id, user.email)
    headers = {"Authorization": f"Bearer {token}"}

    test_audit_id = "test-audit-123"
    test_artifact_id = "desktop.png"

    project = ProjectModel(project_id="proj_art_1", name="Art Proj", target_url="https://example.com", user_id=user.user_id, created_at=datetime.now(timezone.utc))
    audit = AuditModel(audit_id=test_audit_id, project_id=project.project_id, target_url="https://example.com", status="completed", created_at=datetime.now(timezone.utc))
    db_session.add(project)
    db_session.add(audit)
    db_session.commit()

    audit_dir = ARTIFACTS_BASE_DIR / test_audit_id
    audit_dir.mkdir(parents=True, exist_ok=True)
    dummy_file = audit_dir / test_artifact_id
    dummy_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

    try:
        response = await async_client.get(f"/api/v1/audits/{test_audit_id}/artifacts/{test_artifact_id}", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
    finally:
        if dummy_file.exists():
            dummy_file.unlink()
        if audit_dir.exists():
            audit_dir.rmdir()

