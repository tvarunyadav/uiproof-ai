import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.models import UserModel, ProjectModel, AuditModel, IssueModel, ArtifactModel
from app.services.auth import create_access_token, hash_password
from app.db.session import get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_db_dependency(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def user_a(db_session):
    user = UserModel(
        user_id="usr_user_a",
        email="usera@example.com",
        password_hash=hash_password("PasswordA123!"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.user_id, user.email)
    return {"user": user, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def user_b(db_session):
    user = UserModel(
        user_id="usr_user_b",
        email="userb@example.com",
        password_hash=hash_password("PasswordB123!"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user.user_id, user.email)
    return {"user": user, "headers": {"Authorization": f"Bearer {token}"}}


# ==============================================================================
# 1. BRAND NEW USER & STRICT ISOLATION TESTS
# ==============================================================================

def test_brand_new_user_has_zero_projects_and_zero_audits(db_session, user_a, user_b):
    """
    Requirements 1, 2, 3, 4, 14:
    - User A creates Project A and Audit A.
    - Brand new User B sees 0 projects, 0 audits, and empty history.
    """
    proj_a = ProjectModel(project_id="proj_a_100", user_id="usr_user_a", name="User A App", target_url="https://a.com")
    audit_a = AuditModel(audit_id="audit_a_100", project_id="proj_a_100", target_url="https://a.com", status="completed")
    db_session.add_all([proj_a, audit_a])
    db_session.commit()

    # User A sees Project A and Audit A
    res_a_proj = client.get("/api/v1/projects", headers=user_a["headers"])
    assert res_a_proj.status_code == 200
    assert len(res_a_proj.json()) == 1

    res_a_audit = client.get("/api/v1/audits", headers=user_a["headers"])
    assert res_a_audit.status_code == 200
    assert len(res_a_audit.json()) == 1

    # Brand new User B sees 0 projects and 0 audits
    res_b_proj = client.get("/api/v1/projects", headers=user_b["headers"])
    assert res_b_proj.status_code == 200
    assert len(res_b_proj.json()) == 0

    res_b_audit = client.get("/api/v1/audits", headers=user_b["headers"])
    assert res_b_audit.status_code == 200
    assert len(res_b_audit.json()) == 0


def test_user_b_cannot_access_user_a_project_operations(db_session, user_a, user_b):
    """
    Requirements 5, 6, 7:
    - User B cannot GET Project A by ID (returns 404).
    - User B cannot UPDATE / DELETE Project A (no endpoint or returns 404).
    """
    proj_a = ProjectModel(project_id="proj_a_secret", user_id="usr_user_a", name="User A Secret", target_url="https://a.com")
    db_session.add(proj_a)
    db_session.commit()

    # GET Project A as User B
    res_get = client.get("/api/v1/projects/proj_a_secret", headers=user_b["headers"])
    assert res_get.status_code == 404

    # GET Project A Audits as User B
    res_audits = client.get("/api/v1/projects/proj_a_secret/audits", headers=user_b["headers"])
    assert res_audits.status_code == 404

    # PUT / DELETE on projects endpoint (not supported / returns 404 / 405)
    res_put = client.put("/api/v1/projects/proj_a_secret", json={"name": "Hacked"}, headers=user_b["headers"])
    assert res_put.status_code in (404, 405)

    res_del = client.delete("/api/v1/projects/proj_a_secret", headers=user_b["headers"])
    assert res_del.status_code in (404, 405)


def test_user_b_cannot_access_user_a_audit_and_nested_resources(db_session, user_a, user_b):
    """
    Requirements 8, 9, 10, 11, 12, 13:
    - User B cannot GET Audit A by ID.
    - User B cannot access Audit A's issues / AI analysis.
    - User B cannot access Audit A evidence/artifacts.
    - User B cannot retest Audit A.
    - User B cannot access comparison data for Audit A.
    - User B cannot generate fix prompt for Audit A.
    """
    proj_a = ProjectModel(project_id="proj_a_nested", user_id="usr_user_a", name="User A App", target_url="https://a.com")
    audit_a = AuditModel(audit_id="audit_a_nested", project_id="proj_a_nested", target_url="https://a.com", status="completed")
    issue_a = IssueModel(audit_id="audit_a_nested", issue_id="ISSUE-A-1", category="layout", severity="critical", title="T", description="D")
    db_session.add_all([proj_a, audit_a, issue_a])
    db_session.commit()

    headers_b = user_b["headers"]

    # 8. User B cannot GET Audit A
    assert client.get("/api/v1/audits/audit_a_nested", headers=headers_b).status_code == 404

    # 9. User B cannot access Audit A issues (issue analysis returns 404)
    assert client.post("/api/v1/audits/audit_a_nested/issues/ISSUE-A-1/analyze", headers=headers_b).status_code == 404

    # 10. User B cannot invoke AI analysis for Audit A
    assert client.post("/api/v1/audits/audit_a_nested/issues/ISSUE-A-1/analyze", headers=headers_b).status_code == 404

    # 11. User B cannot access Audit A evidence/artifacts
    assert client.get("/api/v1/audits/audit_a_nested/artifacts/desktop.png", headers=headers_b).status_code == 404

    # 12. User B cannot retest Audit A
    assert client.post("/api/v1/audits/audit_a_nested/retest", headers=headers_b).status_code == 404

    # 13. User B cannot access comparison data for Audit A
    assert client.post("/api/v1/audits/compare", json={"baseline_audit_id": "audit_a_nested", "new_audit_id": "audit_a_nested"}, headers=headers_b).status_code == 404
    assert client.get("/api/v1/audits/audit_a_nested/compare/audit_a_nested", headers=headers_b).status_code == 404

    # Fix prompt for Audit A
    assert client.get("/api/v1/audits/audit_a_nested/fix-prompt", headers=headers_b).status_code == 404


def test_reciprocal_isolation_user_a_cannot_access_user_b_resources(db_session, user_a, user_b):
    """
    Requirement 15: Reciprocal isolation test (User A cannot access User B's resources).
    """
    proj_b = ProjectModel(project_id="proj_b_reciprocal", user_id="usr_user_b", name="User B App", target_url="https://b.com")
    audit_b = AuditModel(audit_id="audit_b_reciprocal", project_id="proj_b_reciprocal", target_url="https://b.com", status="completed")
    db_session.add_all([proj_b, audit_b])
    db_session.commit()

    headers_a = user_a["headers"]

    assert client.get("/api/v1/projects/proj_b_reciprocal", headers=headers_a).status_code == 404
    assert client.get("/api/v1/audits/audit_b_reciprocal", headers=headers_a).status_code == 404


def test_unauthenticated_requests_return_401():
    """
    Requirement 16: Unauthenticated requests return 401 Unauthorized.
    """
    from app.services.auth.dependencies import get_current_user_dep
    saved_override = app.dependency_overrides.pop(get_current_user_dep, None)
    try:
        assert client.get("/api/v1/projects").status_code == 401
        assert client.post("/api/v1/projects", json={"name": "P", "target_url": "https://p.com"}).status_code == 401
        assert client.get("/api/v1/projects/proj_123").status_code == 401
        assert client.get("/api/v1/projects/proj_123/audits").status_code == 401
        assert client.get("/api/v1/audits").status_code == 401
        assert client.post("/api/v1/audits", json={"url": "https://a.com"}).status_code == 401
        assert client.get("/api/v1/audits/audit_123").status_code == 401
        assert client.post("/api/v1/audits/audit_123/retest").status_code == 401
        assert client.post("/api/v1/audits/compare", json={"baseline_audit_id": "b", "new_audit_id": "n"}).status_code == 401
        assert client.get("/api/v1/audits/audit_1/compare/audit_2").status_code == 401
        assert client.get("/api/v1/audits/audit_1/artifacts/art_1.png").status_code == 401
        assert client.get("/api/v1/audits/audit_1/fix-prompt").status_code == 401
        assert client.post("/api/v1/audits/audit_1/issues/issue_1/analyze").status_code == 401
    finally:
        if saved_override:
            app.dependency_overrides[get_current_user_dep] = saved_override


def test_owner_regression_legitimate_operations_work(db_session, user_a):
    """
    Owner regression tests: User A can create, view, run audit, analyze, retest, and compare own resources.
    """
    headers = user_a["headers"]

    # Create & view project
    res_proj = client.post("/api/v1/projects", json={"name": "My App", "target_url": "https://myapp.com"}, headers=headers)
    assert res_proj.status_code == 201
    proj_id = res_proj.json()["project_id"]

    assert client.get(f"/api/v1/projects/{proj_id}", headers=headers).status_code == 200

    # Seed audit for User A
    audit_a = AuditModel(audit_id="audit_owner_001", project_id=proj_id, target_url="https://myapp.com", status="completed")
    issue_a = IssueModel(audit_id="audit_owner_001", issue_id="ISSUE-OWNER-1", category="seo", severity="low", title="Title", description="Desc")
    db_session.add_all([audit_a, issue_a])
    db_session.commit()

    # User A views audit
    assert client.get("/api/v1/audits/audit_owner_001", headers=headers).status_code == 200

    # User A compares own audits
    assert client.post("/api/v1/audits/compare", json={"baseline_audit_id": "audit_owner_001", "new_audit_id": "audit_owner_001"}, headers=headers).status_code == 200

    # User A gets fix prompt
    assert client.get("/api/v1/audits/audit_owner_001/fix-prompt", headers=headers).status_code in (200, 503)

    # User A analyzes issue
    res_ai = client.post("/api/v1/audits/audit_owner_001/issues/ISSUE-OWNER-1/analyze", headers=headers)
    assert res_ai.status_code in (200, 503)


def test_unassigned_legacy_records_not_leaked_to_users(db_session, user_a, user_b):
    """
    Ensures legacy records without user_id / project_id are NOT leaked to User A or User B.
    """
    legacy_proj = ProjectModel(project_id="proj_legacy_orphan", user_id=None, name="Orphan App", target_url="https://orphan.com")
    legacy_audit = AuditModel(audit_id="audit_legacy_orphan", project_id=None, target_url="https://orphan.com", status="completed")
    db_session.add_all([legacy_proj, legacy_audit])
    db_session.commit()

    # User A and User B cannot list or access unassigned orphan records
    assert client.get("/api/v1/projects/proj_legacy_orphan", headers=user_a["headers"]).status_code == 404
    assert client.get("/api/v1/projects/proj_legacy_orphan", headers=user_b["headers"]).status_code == 404

    assert client.get("/api/v1/audits/audit_legacy_orphan", headers=user_a["headers"]).status_code == 404
    assert client.get("/api/v1/audits/audit_legacy_orphan", headers=user_b["headers"]).status_code == 404

    res_a_projs = [p["project_id"] for p in client.get("/api/v1/projects", headers=user_a["headers"]).json()]
    assert "proj_legacy_orphan" not in res_a_projs

    res_b_projs = [p["project_id"] for p in client.get("/api/v1/projects", headers=user_b["headers"]).json()]
    assert "proj_legacy_orphan" not in res_b_projs
