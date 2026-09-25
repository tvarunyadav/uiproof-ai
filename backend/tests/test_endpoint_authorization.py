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
# 1. UNAUTHENTICATED PROTECTION TESTS (401)
# ==============================================================================

def test_unauthenticated_requests_return_401():
    """
    Test 1: Unauthenticated requests to protected project & audit routes return 401.
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



# ==============================================================================
# 2. PROJECT AUTHORIZATION & ISOLATION TESTS
# ==============================================================================

def test_user_sees_own_projects_and_cannot_access_other_user_projects(db_session, user_a, user_b):
    """
    Tests 2, 3, 4, 5, 6:
    - User A can create and list own projects.
    - User A cannot see User B's projects in GET /projects list.
    - User A requesting User B's project returns 404.
    - User A requesting User B's project audits returns 404.
    """
    proj_a = ProjectModel(project_id="proj_a_100", user_id="usr_user_a", name="User A App", target_url="https://a.com")
    proj_b = ProjectModel(project_id="proj_b_200", user_id="usr_user_b", name="User B App", target_url="https://b.com")
    db_session.add_all([proj_a, proj_b])
    db_session.commit()

    # User A listing projects (Test 2 & 3)
    res_a_list = client.get("/api/v1/projects", headers=user_a["headers"])
    assert res_a_list.status_code == 200
    a_proj_ids = [p["project_id"] for p in res_a_list.json()]
    assert "proj_a_100" in a_proj_ids
    assert "proj_b_200" not in a_proj_ids  # Test 4: User A does not see User B's project

    # User A getting own project
    assert client.get("/api/v1/projects/proj_a_100", headers=user_a["headers"]).status_code == 200

    # User A getting User B's project (Test 5)
    assert client.get("/api/v1/projects/proj_b_200", headers=user_a["headers"]).status_code == 404

    # User A getting User B's project audits (Test 6)
    assert client.get("/api/v1/projects/proj_b_200/audits", headers=user_a["headers"]).status_code == 404


def test_user_cannot_create_audit_under_other_user_project(db_session, user_a, user_b):
    """
    Test 7: User A cannot create an audit associated with User B's project ID (returns 404).
    """
    proj_b = ProjectModel(project_id="proj_b_private", user_id="usr_user_b", name="User B Private", target_url="https://b.com")
    db_session.add(proj_b)
    db_session.commit()

    res = client.post("/api/v1/audits", json={"url": "https://b.com", "project_id": "proj_b_private"}, headers=user_a["headers"])
    assert res.status_code == 404


# ==============================================================================
# 3. AUDIT AUTHORIZATION & IDOR TESTS
# ==============================================================================

def test_audit_cross_user_idor_protections(db_session, user_a, user_b):
    """
    Tests 8, 9, 10, 11, 12, 13, 14:
    User A attempting to access User B's audit, retest, compare, artifact, fix-prompt, or issue analysis returns 404.
    """
    proj_b = ProjectModel(project_id="proj_b_300", user_id="usr_user_b", name="User B App", target_url="https://b.com")
    audit_b = AuditModel(audit_id="audit_b_300", project_id="proj_b_300", target_url="https://b.com", status="completed")
    issue_b = IssueModel(audit_id="audit_b_300", issue_id="ISSUE-B-1", category="layout", severity="high", title="T", description="D")
    db_session.add_all([proj_b, audit_b, issue_b])
    db_session.commit()

    headers_a = user_a["headers"]

    # Test 8: User A cannot GET User B's audit
    assert client.get("/api/v1/audits/audit_b_300", headers=headers_a).status_code == 404

    # Test 9: User A cannot retest User B's audit
    assert client.post("/api/v1/audits/audit_b_300/retest", headers=headers_a).status_code == 404

    # Test 10: User A cannot compare User B's audits
    assert client.post("/api/v1/audits/compare", json={"baseline_audit_id": "audit_b_300", "new_audit_id": "audit_b_300"}, headers=headers_a).status_code == 404

    # Test 11: User A cannot compare User A's audit with User B's audit
    proj_a = ProjectModel(project_id="proj_a_300", user_id="usr_user_a", name="User A App", target_url="https://a.com")
    audit_a = AuditModel(audit_id="audit_a_300", project_id="proj_a_300", target_url="https://a.com", status="completed")
    db_session.add_all([proj_a, audit_a])
    db_session.commit()
    assert client.post("/api/v1/audits/compare", json={"baseline_audit_id": "audit_a_300", "new_audit_id": "audit_b_300"}, headers=headers_a).status_code == 404

    # Test 12: User A cannot download User B's artifact
    assert client.get("/api/v1/audits/audit_b_300/artifacts/desktop.png", headers=headers_a).status_code == 404

    # Test 13: User A cannot generate User B's fix prompt
    assert client.get("/api/v1/audits/audit_b_300/fix-prompt", headers=headers_a).status_code == 404

    # Test 14: User A cannot trigger AI analysis on User B's issue
    assert client.post("/api/v1/audits/audit_b_300/issues/ISSUE-B-1/analyze", headers=headers_a).status_code == 404


# ==============================================================================
# 4. AUTHORIZED OWNER SUCCESS TESTS
# ==============================================================================

def test_user_can_access_own_resources(db_session, user_a):
    """
    Tests 15, 16, 18, 20: User A can successfully access own project, audit, compare, and issue analysis.
    """
    headers = user_a["headers"]

    # Test 15: Create & GET own project
    create_res = client.post("/api/v1/projects", json={"name": "My App", "target_url": "https://myapp.com"}, headers=headers)
    assert create_res.status_code == 201
    proj_id = create_res.json()["project_id"]
    assert client.get(f"/api/v1/projects/{proj_id}", headers=headers).status_code == 200

    # Seed an audit for User A
    audit_a = AuditModel(audit_id="audit_my_001", project_id=proj_id, target_url="https://myapp.com", status="completed")
    issue_a = IssueModel(audit_id="audit_my_001", issue_id="ISSUE-MY-1", category="seo", severity="low", title="Title", description="Desc")
    db_session.add_all([audit_a, issue_a])
    db_session.commit()

    # Test 16: User A can GET own audit
    assert client.get("/api/v1/audits/audit_my_001", headers=headers).status_code == 200

    # Test 18: User A can compare own audits
    assert client.post("/api/v1/audits/compare", json={"baseline_audit_id": "audit_my_001", "new_audit_id": "audit_my_001"}, headers=headers).status_code == 200

    # Test 20: User A can analyze own issue
    res_ai = client.post("/api/v1/audits/audit_my_001/issues/ISSUE-MY-1/analyze", headers=headers)
    assert res_ai.status_code in (200, 538, 503)  # 200 OK or 503 AI not configured (both prove authorization passed)


# ==============================================================================
# 5. LEGACY NULL-OWNERSHIP COMPATIBILITY TESTS
# ==============================================================================

def test_legacy_null_owned_records_remain_accessible(db_session, user_a):
    """
    Tests 21, 22: Legacy projects (user_id IS NULL) and legacy audits (project_id IS NULL) remain accessible.
    """
    headers = user_a["headers"]

    legacy_proj = ProjectModel(project_id="proj_legacy_999", user_id=None, name="Legacy App", target_url="https://legacy.com")
    legacy_audit = AuditModel(audit_id="audit_legacy_999", project_id="proj_legacy_999", target_url="https://legacy.com", status="completed")
    unassigned_audit = AuditModel(audit_id="audit_unassigned_999", project_id=None, target_url="https://unassigned.com", status="completed")

    db_session.add_all([legacy_proj, legacy_audit, unassigned_audit])
    db_session.commit()

    # Test 21: Legacy NULL-owned project remains accessible
    assert client.get("/api/v1/projects/proj_legacy_999", headers=headers).status_code == 200

    # Test 22: Legacy NULL-owned audit remains accessible
    assert client.get("/api/v1/audits/audit_legacy_999", headers=headers).status_code == 200
    assert client.get("/api/v1/audits/audit_unassigned_999", headers=headers).status_code == 200
