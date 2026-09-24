import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from app.schemas.audit import (
    CreateAuditRequest,
    AuditResult,
    AuditComparison,
    DeveloperFixPrompt,
    RetestAuditResponse,
)
from app.schemas.ai import IssueAnalysisResponse
from app.services.ai.interface import AINotConfiguredError, AIProviderError
from app.services.audit import audit_engine
from app.utils.security import validate_and_sanitize_url

router = APIRouter()

# Path to backend/artifacts directory
ARTIFACTS_BASE_DIR = Path(__file__).resolve().parents[4] / "artifacts"


class AuditComparisonRequest(BaseModel):
    baseline_audit_id: str
    new_audit_id: str


@router.post("", response_model=AuditResult, status_code=status.HTTP_201_CREATED, tags=["Audits"])
async def create_audit(request: CreateAuditRequest):
    """
    Trigger a new web application quality assurance audit.
    Executes Playwright Chromium, collects browser evidence across viewports, and produces structured issues.
    """
    # Enforce URL scheme validation & SSRF protection
    sanitized_url = validate_and_sanitize_url(request.url)
    request.url = sanitized_url

    result = await audit_engine.create_audit(request)
    if result.status == "failed" and result.error_message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audit execution failed: {result.error_message}"
        )
    return result


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


@router.post("/{audit_id}/retest", response_model=RetestAuditResponse, status_code=status.HTTP_201_CREATED, tags=["Audits"])
async def retest_audit(audit_id: str):
    """
    Re-run Playwright audit using the baseline audit's URL and viewports.
    Returns both the newly generated retest audit and deterministic comparison.
    """
    try:
        retest_audit_result, comparison = await audit_engine.retest_audit(audit_id)
        return RetestAuditResponse(
            retest_audit=retest_audit_result,
            comparison=comparison
        )
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err).strip("'\"")
        )


@router.get("/{audit_id}/artifacts/{artifact_id}", tags=["Audits"])
async def get_audit_artifact(audit_id: str, artifact_id: str):
    """
    Safely serve generated audit artifacts (e.g. screenshots) from controlled directory.
    Enforces strict path traversal prevention.
    """
    # Sanitize inputs against path traversal attacks
    safe_audit_id = os.path.basename(audit_id.strip())
    safe_artifact_id = os.path.basename(artifact_id.strip())

    if safe_audit_id != audit_id or safe_artifact_id != artifact_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid artifact identifier format."
        )

    artifact_path = (ARTIFACTS_BASE_DIR / safe_audit_id / safe_artifact_id).resolve()

    # Ensure path stays strictly within ARTIFACTS_BASE_DIR
    try:
        artifact_path.relative_to(ARTIFACTS_BASE_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to specified filepath is forbidden."
        )

    if not artifact_path.exists() or not artifact_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{safe_artifact_id}' for audit '{safe_audit_id}' was not found."
        )

    return FileResponse(
        path=str(artifact_path),
        media_type="image/png",
        filename=safe_artifact_id
    )


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


@router.get("/{audit_id}/compare/{retest_id}", response_model=AuditComparison, tags=["Audits"])
async def get_audit_comparison(audit_id: str, retest_id: str):
    """
    Retrieve deterministic comparison between baseline audit (audit_id) and retest audit (retest_id).
    """
    comparison = audit_engine.compare_audits(
        baseline_id=audit_id,
        new_id=retest_id
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


@router.post("/{audit_id}/issues/{issue_id}/analyze", response_model=IssueAnalysisResponse, tags=["AI Analysis"])
async def analyze_audit_issue(audit_id: str, issue_id: str):
    """
    Analyze an existing verified deterministic issue using the configured AI provider.
    Returns structured AI diagnostics, likely causes, constraints, and fix prompts.
    """
    try:
        return await audit_engine.analyze_issue(audit_id=audit_id, issue_id=issue_id)
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err).strip("'\"")
        )
    except AINotConfiguredError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "AI_NOT_CONFIGURED", "message": str(err)}
        )
    except AIProviderError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "AI_PROVIDER_ERROR", "message": str(err)}
        )


