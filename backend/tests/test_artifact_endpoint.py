import pytest
from datetime import datetime, timezone
from pathlib import Path
from app.api.v1.endpoints.audits import ARTIFACTS_BASE_DIR
from app.db.models import UserModel, ProjectModel, AuditModel
from app.services.auth import create_access_token, hash_password


@pytest.mark.asyncio
async def test_artifact_unauthenticated_request_returns_401(async_client):
    """
    Test 1: Unauthenticated request to artifact endpoint returns 401 Unauthorized.
    """
    response = await async_client.get("/api/v1/audits/any-audit-id/artifacts/desktop.png")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_artifact_path_traversal_rejection(async_client):
    response = await async_client.get("/api/v1/audits/../../etc/artifacts/desktop.png")
    assert response.status_code in (404, 401, 400, 422)


@pytest.mark.asyncio
async def test_artifact_serving_authenticated_owner(async_client, db_session):
    """
    Test 2 & 5: Authenticated owner can retrieve artifact with Bearer token headers.
    """
    user = UserModel(user_id="usr_art_owner", email="art_owner@example.com", password_hash=hash_password("Pass123!"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.user_id, user.email)
    headers = {"Authorization": f"Bearer {token}"}

    test_audit_id = "test-audit-owner-123"
    test_artifact_id = "desktop.png"

    project = ProjectModel(project_id="proj_art_owner", name="Art Owner Proj", target_url="https://example.com", user_id=user.user_id, created_at=datetime.now(timezone.utc))
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
        assert len(response.content) > 0
    finally:
        if dummy_file.exists():
            dummy_file.unlink()
        if audit_dir.exists():
            audit_dir.rmdir()


@pytest.mark.asyncio
async def test_artifact_authenticated_non_owner_denied(async_client, db_session):
    """
    Test 3: Authenticated non-owner is denied access to an audit artifact.
    """
    owner = UserModel(user_id="usr_owner_orig", email="owner_orig@example.com", password_hash=hash_password("Pass123!"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    other_user = UserModel(user_id="usr_other_user", email="other_user@example.com", password_hash=hash_password("Pass123!"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    db_session.add(owner)
    db_session.add(other_user)
    db_session.commit()

    project = ProjectModel(project_id="proj_owner_only", name="Owner Only", target_url="https://example.com", user_id=owner.user_id, created_at=datetime.now(timezone.utc))
    audit = AuditModel(audit_id="audit-owner-only-99", project_id=project.project_id, target_url="https://example.com", status="completed", created_at=datetime.now(timezone.utc))
    db_session.add(project)
    db_session.add(audit)
    db_session.commit()

    # Request with other_user's token
    other_token = create_access_token(other_user.user_id, other_user.email)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = await async_client.get("/api/v1/audits/audit-owner-only-99/artifacts/desktop.png", headers=other_headers)
    # Non-owner receives 404 (IDOR privacy protection) or 403
    assert response.status_code in (404, 403)


@pytest.mark.asyncio
async def test_artifact_invalid_audit_or_artifact_error(async_client, db_session):
    """
    Test 4: Invalid audit or artifact identifier format returns correct error.
    """
    user = UserModel(user_id="usr_art_invalid", email="art_invalid@example.com", password_hash=hash_password("Pass123!"), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.user_id, user.email)
    headers = {"Authorization": f"Bearer {token}"}

    # Non-existent audit ID -> 404
    res1 = await async_client.get("/api/v1/audits/non-existent-audit-id-0000/artifacts/desktop.png", headers=headers)
    assert res1.status_code == 404

    # Invalid artifact format (path separator) -> 400
    res2 = await async_client.get("/api/v1/audits/test-audit-id/artifacts/subfolder/desktop.png", headers=headers)
    assert res2.status_code in (400, 404, 422)
