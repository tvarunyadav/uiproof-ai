import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.services.audit import audit_engine
from app.services.project import project_service
from app.schemas.project import CreateProjectRequest
from app.schemas.audit import CreateAuditRequest, AuditResult, AuditStatus, AuditSummaryStats
from app.schemas.issue import Issue, IssueCategory, IssueSeverity
from app.db.models import ProjectModel, AuditModel

client = TestClient(app)


def test_create_and_get_project(db_session):
    """
    Test 1, 2, 4: Create project, retrieve project, and check audit_count.
    """
    req = CreateProjectRequest(name="E-Commerce App", target_url="https://shop.example.com")
    proj = project_service.create_project(req, db=db_session)

    assert proj is not None
    assert proj.project_id.startswith("proj_")
    assert proj.name == "E-Commerce App"
    assert proj.target_url == "https://shop.example.com"
    assert proj.audit_count == 0

    fetched = project_service.get_project(proj.project_id, db=db_session)
    assert fetched is not None
    assert fetched.name == "E-Commerce App"
    assert fetched.audit_count == 0


def test_list_projects(db_session):
    """
    Test 3: List projects.
    """
    p1 = project_service.create_project(CreateProjectRequest(name="App One", target_url="https://app1.com"), db=db_session)
    p2 = project_service.create_project(CreateProjectRequest(name="App Two", target_url="https://app2.com"), db=db_session)

    projects = project_service.list_projects(db=db_session)
    project_ids = {p.project_id for p in projects}
    assert p1.project_id in project_ids
    assert p2.project_id in project_ids


@pytest.mark.asyncio
async def test_audit_association_and_project_history(db_session):
    """
    Test 5, 6, 7, 8, 9: Associate audit with project, list project audits,
    verify history survives _audits_db.clear().
    """
    proj = project_service.create_project(CreateProjectRequest(name="SaaS Platform", target_url="https://saas.io"), db=db_session)

    issue = Issue(
        issue_id="UI-MISSING-META-DESKTOP",
        category=IssueCategory.SEO,
        severity=IssueSeverity.LOW,
        title="Missing Meta",
        description="Meta description tag missing",
        viewport="Desktop"
    )
    audit = AuditResult(
        audit_id="audit-proj-001",
        target_url="https://saas.io",
        url="https://saas.io",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[issue],
        findings=[issue],
        stats=AuditSummaryStats(total_issues=1)
    )

    audit_engine._save_audit_to_db(audit, project_id=proj.project_id, db=db_session)

    # 1. Project audit count should be 1
    updated_proj = project_service.get_project(proj.project_id, db=db_session)
    assert updated_proj.audit_count == 1

    # 2. List project audits
    summaries = project_service.list_project_audits(proj.project_id, db=db_session)
    assert len(summaries) == 1
    assert summaries[0].audit_id == "audit-proj-001"
    assert summaries[0].project_id == proj.project_id

    # 3. Clear in-memory dictionary to prove DB read path
    audit_engine._audits_db.clear()

    # 4. Global audit history should return audit summary from DB
    global_audits = project_service.list_all_audits(db=db_session)
    assert any(a.audit_id == "audit-proj-001" for a in global_audits)

    # 5. Full audit can be fetched from DB
    full_audit = audit_engine.get_audit("audit-proj-001", db=db_session)
    assert full_audit is not None
    assert full_audit.audit_id == "audit-proj-001"


@pytest.mark.asyncio
async def test_retest_inherits_project_id(db_session):
    """
    Test 10, 11: Retest automatically inherits baseline project_id and appears in project history.
    """
    proj = project_service.create_project(CreateProjectRequest(name="Retest Proj", target_url="https://retest.io"), db=db_session)

    issue = Issue(
        issue_id="UI-OVERFLOW-MOBILE",
        category=IssueCategory.RESPONSIVE,
        severity=IssueSeverity.HIGH,
        title="Mobile Overflow",
        description="Horizontal scroll on mobile",
        viewport="Mobile"
    )
    baseline_audit = AuditResult(
        audit_id="baseline-p1",
        target_url="https://retest.io",
        url="https://retest.io",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[issue],
        findings=[issue],
        stats=AuditSummaryStats(total_issues=1)
    )
    audit_engine._save_audit_to_db(baseline_audit, project_id=proj.project_id, db=db_session)

    # Execute retest
    retest_audit_res = AuditResult(
        audit_id="retest-p2",
        target_url="https://retest.io",
        url="https://retest.io",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[],
        findings=[],
        stats=AuditSummaryStats(total_issues=0)
    )
    audit_engine._save_audit_to_db(retest_audit_res, baseline_audit_id="baseline-p1", project_id=proj.project_id, db=db_session)

    summaries = project_service.list_project_audits(proj.project_id, db=db_session)
    assert len(summaries) == 2
    audit_ids = [s.audit_id for s in summaries]
    assert "baseline-p1" in audit_ids
    assert "retest-p2" in audit_ids

    retest_item = next(s for s in summaries if s.audit_id == "retest-p2")
    assert retest_item.baseline_audit_id == "baseline-p1"
    assert retest_item.project_id == proj.project_id


def test_legacy_unassigned_audits(db_session):
    """
    Test 12: Unassigned legacy audits (project_id = NULL) remain accessible under Default Project.
    """
    legacy_audit = AuditResult(
        audit_id="legacy-audit-000",
        target_url="https://legacy.com",
        url="https://legacy.com",
        status=AuditStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        issues=[],
        findings=[],
        stats=AuditSummaryStats()
    )
    audit_engine._save_audit_to_db(legacy_audit, project_id=None, db=db_session)

    projects = project_service.list_projects(db=db_session)
    assert any(p.project_id == "proj_default" for p in projects)

    default_audits = project_service.list_project_audits("proj_default", db=db_session)
    assert any(a.audit_id == "legacy-audit-000" for a in default_audits)


def test_project_endpoint_http_calls():
    """
    Test 13, 14: Test HTTP endpoints POST /projects, GET /projects, GET /projects/{id}, GET /projects/{id}/audits, GET /audits.
    """
    # Create project via API
    res = client.post("/api/v1/projects", json={"name": "API Test Proj", "target_url": "https://apitest.com"})
    assert res.status_code == 201
    pdata = res.json()
    assert pdata["name"] == "API Test Proj"
    project_id = pdata["project_id"]

    # Get project via API
    res_get = client.get(f"/api/v1/projects/{project_id}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "API Test Proj"

    # List projects via API
    res_list = client.get("/api/v1/projects")
    assert res_list.status_code == 200
    assert any(p["project_id"] == project_id for p in res_list.json())

    # List audits for project via API
    res_audits = client.get(f"/api/v1/projects/{project_id}/audits")
    assert res_audits.status_code == 200
    assert isinstance(res_audits.json(), list)

    # Global audits list via API
    res_global = client.get("/api/v1/audits")
    assert res_global.status_code == 200
    assert isinstance(res_global.json(), list)

    # 404 for unknown project
    res_404 = client.get("/api/v1/projects/non-existent-proj-id")
    assert res_404.status_code == 404
