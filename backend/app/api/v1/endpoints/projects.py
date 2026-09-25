from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.schemas.project import Project, CreateProjectRequest, AuditSummaryItem
from app.services.project import project_service
from app.services.auth import get_current_user_dep
from app.db.models import UserModel
from app.db.session import get_db

router = APIRouter()


@router.get("", response_model=List[Project], tags=["Projects"])
async def list_projects(
    current_user: UserModel = Depends(get_current_user_dep),
    db: Session = Depends(get_db)
):
    """
    List all persistent projects owned by the current user (plus legacy unassigned projects).
    """
    return project_service.list_projects(user_id=current_user.user_id, db=db)


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED, tags=["Projects"])
async def create_project(
    request: CreateProjectRequest,
    current_user: UserModel = Depends(get_current_user_dep),
    db: Session = Depends(get_db)
):
    """
    Create a new project workspace associated with the authenticated user.
    """
    if not request.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project name cannot be empty.")
    if not request.target_url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project target URL cannot be empty.")

    return project_service.create_project(request, user_id=current_user.user_id, db=db)


@router.get("/{project_id}", response_model=Project, tags=["Projects"])
async def get_project(
    project_id: str,
    current_user: UserModel = Depends(get_current_user_dep),
    db: Session = Depends(get_db)
):
    """
    Retrieve project details by project ID if owned by current user or legacy unassigned.
    """
    project = project_service.get_project(project_id, user_id=current_user.user_id, db=db)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    return project


@router.get("/{project_id}/audits", response_model=List[AuditSummaryItem], tags=["Projects"])
async def list_project_audits(
    project_id: str,
    current_user: UserModel = Depends(get_current_user_dep),
    db: Session = Depends(get_db)
):
    """
    List lightweight audit history for a specific project ordered newest first.
    """
    audits = project_service.list_project_audits(project_id, user_id=current_user.user_id, db=db)
    if audits is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    return audits



