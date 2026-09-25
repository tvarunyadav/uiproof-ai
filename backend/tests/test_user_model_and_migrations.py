import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.db.models import UserModel, ProjectModel, AuditModel, IssueModel, AIAnalysisModel, ArtifactModel
from app.schemas.audit import AuditStatus


def test_user_model_insertion_and_fields(db_session):
    """
    Test 1, 2: Verify UserModel table exists and a User can be inserted with valid fields.
    """
    user = UserModel(
        user_id="usr_test123",
        email="developer@example.com",
        password_hash="hashed_secret_password",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()

    fetched = db_session.query(UserModel).filter_by(user_id="usr_test123").first()
    assert fetched is not None
    assert fetched.email == "developer@example.com"
    assert fetched.password_hash == "hashed_secret_password"


def test_user_email_uniqueness(db_session):
    """
    Test 3: Email uniqueness constraint is enforced on UserModel.
    """
    user1 = UserModel(
        user_id="usr_001",
        email="unique@example.com",
        password_hash="hash1",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user1)
    db_session.commit()

    user2 = UserModel(
        user_id="usr_002",
        email="unique@example.com",
        password_hash="hash2",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_project_user_relationship(db_session):
    """
    Test 4, 5, 6, 7: Verify Project.user_id can be NULL, and User <-> Project relationship works when linked.
    """
    # 1. Unassigned project (user_id = None)
    unassigned_project = ProjectModel(
        project_id="proj_unassigned",
        user_id=None,
        name="Unassigned App",
        target_url="https://unassigned.com",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(unassigned_project)
    db_session.commit()

    fetched_unassigned = db_session.query(ProjectModel).filter_by(project_id="proj_unassigned").first()
    assert fetched_unassigned is not None
    assert fetched_unassigned.user_id is None
    assert fetched_unassigned.user is None

    # 2. Linked user project
    owner = UserModel(
        user_id="usr_owner",
        email="owner@domain.com",
        password_hash="secret_hash",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(owner)
    db_session.commit()

    owned_project = ProjectModel(
        project_id="proj_owned",
        user_id=owner.user_id,
        name="Owned App",
        target_url="https://owned.com",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(owned_project)
    db_session.commit()

    # 3. Test Project.user back-reference
    fetched_owned = db_session.query(ProjectModel).filter_by(project_id="proj_owned").first()
    assert fetched_owned is not None
    assert fetched_owned.user is not None
    assert fetched_owned.user.email == "owner@domain.com"

    # 4. Test User.projects collection relationship
    fetched_user = db_session.query(UserModel).filter_by(user_id="usr_owner").first()
    assert fetched_user is not None
    assert len(fetched_user.projects) == 1
    assert fetched_user.projects[0].project_id == "proj_owned"


def test_existing_relationships_integrity(db_session):
    """
    Test 8, 9, 10: Verify existing Project -> Audit -> Issue/AIAnalysis/Artifact relationships remain intact.
    """
    proj = ProjectModel(project_id="p_rel_1", name="Rel App", target_url="https://rel.com", created_at=datetime.now(timezone.utc))
    db_session.add(proj)

    audit = AuditModel(audit_id="a_rel_1", project_id="p_rel_1", target_url="https://rel.com", status="completed", created_at=datetime.now(timezone.utc))
    db_session.add(audit)

    issue = IssueModel(issue_id="UI-01", audit_id="a_rel_1", category="responsive", severity="high", title="Title", description="Desc")
    db_session.add(issue)

    ai = AIAnalysisModel(audit_id="a_rel_1", issue_id="UI-01", summary="AI Summary", expected_result="Expected", fix_prompt="Fix Prompt")
    db_session.add(ai)

    art = ArtifactModel(artifact_id="art-01", audit_id="a_rel_1", file_path="/artifacts/a_rel_1/shot.png")
    db_session.add(art)

    db_session.commit()

    fetched_audit = db_session.query(AuditModel).filter_by(audit_id="a_rel_1").first()
    assert fetched_audit is not None
    assert fetched_audit.project.project_id == "p_rel_1"
    assert len(fetched_audit.issues) == 1
    assert len(fetched_audit.ai_analyses) == 1
    assert len(fetched_audit.artifacts) == 1
