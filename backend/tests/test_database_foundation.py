import pytest
import uuid
from datetime import datetime
from sqlalchemy import create_engine, inspect
from app.db.session import Base
from app.db.models import (
    ProjectModel,
    AuditModel,
    IssueModel,
    AIAnalysisModel,
    ArtifactModel,
)


def test_database_engine_initialization_and_table_creation():
    """
    Test 1 & 2: Database engine can initialize and tables can be created.
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert "projects" in tables
    assert "audits" in tables
    assert "issues" in tables
    assert "ai_analyses" in tables
    assert "artifacts" in tables


def test_project_insertion(db_session):
    """
    Test 3: A Project can be inserted.
    """
    project = ProjectModel(
        project_id=f"prj_{uuid.uuid4().hex[:8]}",
        name="Test Web App",
        target_url="http://localhost:3000"
    )
    db_session.add(project)
    db_session.commit()
    
    retrieved = db_session.query(ProjectModel).filter_by(project_id=project.project_id).first()
    assert retrieved is not None
    assert retrieved.name == "Test Web App"
    assert retrieved.target_url == "http://localhost:3000"
    assert isinstance(retrieved.created_at, datetime)


def test_audit_references_project(db_session):
    """
    Test 4: An Audit can reference a Project.
    """
    project = ProjectModel(
        project_id="prj_123",
        name="Audit Target App",
        target_url="http://localhost:3000"
    )
    audit = AuditModel(
        audit_id="audit_abc_123",
        project_id=project.project_id,
        target_url="http://localhost:3000",
        status="completed",
        stats={"total_issues": 2},
        evidence={"screenshot": "path/to/img.png"}
    )
    db_session.add(project)
    db_session.add(audit)
    db_session.commit()

    retrieved_audit = db_session.query(AuditModel).filter_by(audit_id="audit_abc_123").first()
    assert retrieved_audit is not None
    assert retrieved_audit.project is not None
    assert retrieved_audit.project.name == "Audit Target App"
    assert retrieved_audit in project.audits


def test_audit_baseline_self_reference(db_session):
    """
    Test 5: An Audit can reference another Audit through baseline_audit_id.
    """
    baseline = AuditModel(
        audit_id="audit_baseline_001",
        target_url="http://localhost:3000",
        status="completed"
    )
    retest = AuditModel(
        audit_id="audit_retest_002",
        baseline_audit_id=baseline.audit_id,
        target_url="http://localhost:3000",
        status="completed"
    )
    db_session.add(baseline)
    db_session.add(retest)
    db_session.commit()

    retrieved_retest = db_session.query(AuditModel).filter_by(audit_id="audit_retest_002").first()
    assert retrieved_retest is not None
    assert retrieved_retest.baseline_audit is not None
    assert retrieved_retest.baseline_audit.audit_id == "audit_baseline_001"
    assert retrieved_retest in baseline.derived_audits


def test_issue_references_audit(db_session):
    """
    Test 6: An Issue can reference an Audit.
    """
    audit = AuditModel(
        audit_id="audit_with_issue",
        target_url="http://localhost:3000",
        status="completed"
    )
    issue = IssueModel(
        issue_id="UI-OVERFLOW-MOBILE",
        audit_id=audit.audit_id,
        category="responsive",
        severity="high",
        title="Horizontal scroll overflow detected",
        description="Page width exceeds viewport width by 45px",
        selector="div.hero-container",
        viewport="mobile",
        evidence_references=["/artifacts/screenshots/mobile.png"],
        root_cause_analysis="Fixed width 1200px on hero container",
        recommended_fix="Change width to max-width: 100%"
    )
    db_session.add(audit)
    db_session.add(issue)
    db_session.commit()

    retrieved_issue = db_session.query(IssueModel).filter_by(issue_id="UI-OVERFLOW-MOBILE").first()
    assert retrieved_issue is not None
    assert retrieved_issue.audit.audit_id == "audit_with_issue"
    assert retrieved_issue in audit.issues
    assert retrieved_issue.category == "responsive"


def test_ai_analysis_references_audit(db_session):
    """
    Test 7: An AIAnalysis can reference an Audit.
    """
    audit = AuditModel(
        audit_id="audit_with_ai",
        target_url="http://localhost:3000",
        status="completed"
    )
    analysis = AIAnalysisModel(
        audit_id=audit.audit_id,
        issue_id="UI-OVERFLOW-MOBILE",
        summary="Horizontal overflow on mobile viewports",
        likely_causes=["Static pixel width on header element"],
        investigation_hints=["Inspect element styles in DevTools"],
        expected_result="Container wraps cleanly within 390px viewport width",
        constraints=["Do not hide overflow with overflow: hidden"],
        verification_steps=["Resize viewport to 390px and check horizontal scrollbar"],
        fix_prompt="Fix overflow on div.hero-container by converting width to max-width"
    )
    db_session.add(audit)
    db_session.add(analysis)
    db_session.commit()

    retrieved_analysis = db_session.query(AIAnalysisModel).filter_by(audit_id=audit.audit_id).first()
    assert retrieved_analysis is not None
    assert retrieved_analysis.audit.audit_id == "audit_with_ai"
    assert retrieved_analysis in audit.ai_analyses
    assert retrieved_analysis.issue_id == "UI-OVERFLOW-MOBILE"


def test_artifact_references_audit(db_session):
    """
    Test 8: An Artifact can reference an Audit.
    """
    audit = AuditModel(
        audit_id="audit_with_artifact",
        target_url="http://localhost:3000",
        status="completed"
    )
    artifact = ArtifactModel(
        artifact_id="screenshot-desktop-12345",
        audit_id=audit.audit_id,
        viewport="desktop",
        file_path="/artifacts/audits/audit_with_artifact/desktop.png"
    )
    db_session.add(audit)
    db_session.add(artifact)
    db_session.commit()

    retrieved_artifact = db_session.query(ArtifactModel).filter_by(artifact_id="screenshot-desktop-12345").first()
    assert retrieved_artifact is not None
    assert retrieved_artifact.audit.audit_id == "audit_with_artifact"
    assert retrieved_artifact in audit.artifacts
    assert retrieved_artifact.file_path == "/artifacts/audits/audit_with_artifact/desktop.png"
