import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import SessionLocal, init_db
from app.db.models import ProjectModel, AuditModel, IssueModel
from app.schemas.project import Project, CreateProjectRequest, AuditSummaryItem
from app.schemas.audit import AuditStatus

logger = logging.getLogger("uiproof.service.project")

DEFAULT_PROJECT_ID = "proj_default"
DEFAULT_PROJECT_NAME = "Default Project"
DEFAULT_PROJECT_URL = "https://uiproof.local"


class ProjectService:
    """
    Service responsible for Project CRUD operations and Audit History listings.
    """

    def get_or_create_default_project(self, db: Session) -> ProjectModel:
        project = db.query(ProjectModel).filter_by(project_id=DEFAULT_PROJECT_ID).first()
        if not project:
            project = ProjectModel(
                project_id=DEFAULT_PROJECT_ID,
                name=DEFAULT_PROJECT_NAME,
                target_url=DEFAULT_PROJECT_URL,
                created_at=datetime.now(timezone.utc)
            )
            db.add(project)
            db.commit()
            db.refresh(project)
        return project

    def create_project(self, request: CreateProjectRequest, user_id: Optional[str] = None, db: Optional[Session] = None) -> Project:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            project_id = f"proj_{uuid.uuid4().hex[:10]}"
            project_model = ProjectModel(
                project_id=project_id,
                user_id=user_id,
                name=request.name.strip(),
                target_url=request.target_url.strip(),
                created_at=datetime.now(timezone.utc)
            )
            db.add(project_model)
            db.commit()
            db.refresh(project_model)

            return Project(
                project_id=project_model.project_id,
                name=project_model.name,
                target_url=project_model.target_url,
                created_at=project_model.created_at,
                audit_count=0
            )
        finally:
            if close_db:
                db.close()

    def get_project(self, project_id: str, user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[Project]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            if project_id == DEFAULT_PROJECT_ID:
                project_model = self.get_or_create_default_project(db)
            else:
                project_model = db.query(ProjectModel).filter_by(project_id=project_id).first()

            if not project_model:
                return None

            # Ownership check: If project belongs to another user, return None (404)
            if project_model.user_id and user_id and project_model.user_id != user_id:
                return None

            audit_count = db.query(AuditModel).filter_by(project_id=project_model.project_id).count()
            if project_id == DEFAULT_PROJECT_ID:
                null_count = db.query(AuditModel).filter(AuditModel.project_id.is_(None)).count()
                audit_count += null_count

            created_at = project_model.created_at
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            return Project(
                project_id=project_model.project_id,
                name=project_model.name,
                target_url=project_model.target_url,
                created_at=created_at,
                audit_count=audit_count
            )
        finally:
            if close_db:
                db.close()

    def list_projects(self, user_id: Optional[str] = None, db: Optional[Session] = None) -> List[Project]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            projects_data: List[Project] = []
            query = db.query(ProjectModel)
            if user_id:
                query = query.filter((ProjectModel.user_id == user_id) | (ProjectModel.user_id.is_(None)))
            db_projects = query.order_by(ProjectModel.created_at.desc()).all()

            for p in db_projects:
                audit_count = db.query(AuditModel).filter_by(project_id=p.project_id).count()
                if p.project_id == DEFAULT_PROJECT_ID:
                    null_count = db.query(AuditModel).filter(AuditModel.project_id.is_(None)).count()
                    audit_count += null_count

                created_at = p.created_at
                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                projects_data.append(
                    Project(
                        project_id=p.project_id,
                        name=p.name,
                        target_url=p.target_url,
                        created_at=created_at,
                        audit_count=audit_count
                    )
                )

            # Check if there are legacy unassigned audits (project_id IS NULL) and default project not yet in list
            unassigned_count = db.query(AuditModel).filter(AuditModel.project_id.is_(None)).count()
            has_default_in_list = any(p.project_id == DEFAULT_PROJECT_ID for p in projects_data)

            if unassigned_count > 0 and not has_default_in_list:
                def_proj = self.get_or_create_default_project(db)
                total_def_count = db.query(AuditModel).filter(AuditModel.project_id == DEFAULT_PROJECT_ID).count() + unassigned_count
                created_at = def_proj.created_at
                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                projects_data.append(
                    Project(
                        project_id=def_proj.project_id,
                        name=def_proj.name,
                        target_url=def_proj.target_url,
                        created_at=created_at,
                        audit_count=total_def_count
                    )
                )

            return projects_data
        finally:
            if close_db:
                db.close()

    def _convert_audit_to_summary(self, audit_model: AuditModel) -> AuditSummaryItem:
        status_enum = AuditStatus(audit_model.status) if audit_model.status in AuditStatus._value2member_map_ else audit_model.status

        total_issues = 0
        critical_count = 0
        high_count = 0

        if audit_model.stats and isinstance(audit_model.stats, dict):
            total_issues = audit_model.stats.get("total_issues", 0)
            critical_count = audit_model.stats.get("critical_count", 0)
            high_count = audit_model.stats.get("high_count", 0)
        elif audit_model.issues:
            total_issues = len(audit_model.issues)
            critical_count = sum(1 for i in audit_model.issues if i.severity == "critical")
            high_count = sum(1 for i in audit_model.issues if i.severity == "high")

        created_at = audit_model.created_at
        if created_at and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        completed_at = audit_model.completed_at
        if completed_at and completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)

        return AuditSummaryItem(
            audit_id=audit_model.audit_id,
            project_id=audit_model.project_id,
            target_url=audit_model.target_url,
            status=status_enum,
            created_at=created_at,
            completed_at=completed_at,
            total_issues=total_issues,
            critical_count=critical_count,
            high_count=high_count,
            baseline_audit_id=audit_model.baseline_audit_id
        )

    def list_project_audits(self, project_id: str, user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[List[AuditSummaryItem]]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            # Authorize project first
            proj = self.get_project(project_id, user_id=user_id, db=db)
            if not proj:
                return None

            if project_id == DEFAULT_PROJECT_ID:
                audit_models = (
                    db.query(AuditModel)
                    .filter((AuditModel.project_id == DEFAULT_PROJECT_ID) | (AuditModel.project_id.is_(None)))
                    .order_by(AuditModel.created_at.desc())
                    .all()
                )
            else:
                audit_models = (
                    db.query(AuditModel)
                    .filter_by(project_id=project_id)
                    .order_by(AuditModel.created_at.desc())
                    .all()
                )

            return [self._convert_audit_to_summary(a) for a in audit_models]
        finally:
            if close_db:
                db.close()

    def list_all_audits(self, user_id: Optional[str] = None, db: Optional[Session] = None) -> List[AuditSummaryItem]:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            if user_id:
                audit_models = (
                    db.query(AuditModel)
                    .outerjoin(ProjectModel, AuditModel.project_id == ProjectModel.project_id)
                    .filter(
                        (ProjectModel.user_id == user_id) |
                        (ProjectModel.user_id.is_(None)) |
                        (AuditModel.project_id.is_(None))
                    )
                    .order_by(AuditModel.created_at.desc())
                    .all()
                )
            else:
                audit_models = (
                    db.query(AuditModel)
                    .order_by(AuditModel.created_at.desc())
                    .all()
                )
            return [self._convert_audit_to_summary(a) for a in audit_models]
        finally:
            if close_db:
                db.close()



project_service = ProjectService()
