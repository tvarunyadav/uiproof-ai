from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.schemas.audit import (
    CreateAuditRequest,
    AuditResult,
    AuditComparison,
    DeveloperFixPrompt,
)
from app.services.audit import audit_engine

router = APIRouter()


class AuditComparisonRequest(BaseModel):
    baseline_audit_id: str
    new_audit_id: str


@router.post("", response_model=AuditResult, status_code=status.HTTP_201_CREATED, tags=["Audits"])
async def create_audit(request: CreateAuditRequest):
    """
    Trigger a new web application quality assurance audit.
    Collects evidence across viewports and analyzes findings into structured issues.
    """
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must begin with http:// or https://"
        )
    return await audit_engine.create_audit(request)


@router.get("/{audit_id}", response_model=AuditResult, tags=["Audits"])
async def get_audit(audit_id: str):
    """Retrieve audit result details by Audit ID."""
    result = audit_engine.get_audit(audit_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' not found."
        )
    return result


@router.post("/compare", response_model=AuditComparison, tags=["Audits"])
async def compare_audits(request: AuditComparisonRequest):
    """
    Compare a baseline audit with a post-fix re-test audit.
    Identifies fixed issues, remaining issues, new issues, and regressions.
    """
    comparison = audit_engine.compare_audits(
        baseline_id=request.baseline_audit_id,
        new_id=request.new_audit_id
    )
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both audit IDs specified for comparison were not found."
        )
    return comparison


@router.get("/{audit_id}/fix-prompt", response_model=DeveloperFixPrompt, tags=["Audits"])
async def get_developer_fix_prompt(audit_id: str):
    """Generate a structured developer fix prompt for coding tools (Antigravity, Cursor, Claude)."""
    audit = audit_engine.get_audit(audit_id)
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' not found."
        )
    return await audit_engine.ai_provider.generate_fix_prompt(audit_id, audit.issues)
