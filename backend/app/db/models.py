from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    projects = relationship("ProjectModel", back_populates="user", cascade="all, delete-orphan")


class ProjectModel(Base):
    __tablename__ = "projects"

    project_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    target_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="projects")
    audits = relationship(
        "AuditModel",
        back_populates="project",
        cascade="all, delete-orphan"
    )


class AuditModel(Base):
    __tablename__ = "audits"

    audit_id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=True, index=True)
    baseline_audit_id = Column(String, ForeignKey("audits.audit_id"), nullable=True, index=True)
    target_url = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    stats = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    project = relationship("ProjectModel", back_populates="audits")
    baseline_audit = relationship(
        "AuditModel",
        remote_side=[audit_id],
        backref="derived_audits"
    )
    issues = relationship(
        "IssueModel",
        back_populates="audit",
        cascade="all, delete-orphan"
    )
    ai_analyses = relationship(
        "AIAnalysisModel",
        back_populates="audit",
        cascade="all, delete-orphan"
    )
    artifacts = relationship(
        "ArtifactModel",
        back_populates="audit",
        cascade="all, delete-orphan"
    )


class IssueModel(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(String, nullable=False, index=True)
    audit_id = Column(String, ForeignKey("audits.audit_id"), nullable=False, index=True)
    category = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    selector = Column(String, nullable=True)
    viewport = Column(String, nullable=True)
    evidence_references = Column(JSON, nullable=True)
    root_cause_analysis = Column(Text, nullable=True)
    recommended_fix = Column(Text, nullable=True)

    # Relationships
    audit = relationship("AuditModel", back_populates="issues")


class AIAnalysisModel(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String, ForeignKey("audits.audit_id"), nullable=False, index=True)
    issue_id = Column(String, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    likely_causes = Column(JSON, nullable=True)
    investigation_hints = Column(JSON, nullable=True)
    expected_result = Column(Text, nullable=False)
    constraints = Column(JSON, nullable=True)
    verification_steps = Column(JSON, nullable=True)
    fix_prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    audit = relationship("AuditModel", back_populates="ai_analyses")


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    artifact_id = Column(String, primary_key=True, index=True)
    audit_id = Column(String, ForeignKey("audits.audit_id"), nullable=False, index=True)
    viewport = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    audit = relationship("AuditModel", back_populates="artifacts")
