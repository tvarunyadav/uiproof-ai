from fastapi import APIRouter, HTTPException, status
from typing import List

from app.schemas.project import Project, CreateProjectRequest, AuditSummaryItem
from app.services.project import project_service

router = APIRouter()


@router.get("", response_model=List[Project], tags=["Projects"])
async def list_projects():
    """
    List all persistent projects with their audit counts.
    """
    return project_service.list_projects()


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED, tags=["Projects"])
async def create_project(request: CreateProjectRequest):
    """
    Create a new project workspace.
    """
    if not request.name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project name cannot be empty.")
    if not request.target_url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project target URL cannot be empty.")

    return project_service.create_project(request)


@router.get("/{project_id}", response_model=Project, tags=["Projects"])
async def get_project(project_id: str):
    """
    Retrieve project details by project ID.
    """
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    return project


@router.get("/{project_id}/audits", response_model=List[AuditSummaryItem], tags=["Projects"])
async def list_project_audits(project_id: str):
    """
    List lightweight audit history for a specific project ordered newest first.
    """
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )
    return project_service.list_project_audits(project_id)
