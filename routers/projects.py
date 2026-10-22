"""HTTP endpoints for projects."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db, require_manager_or_admin
from models import User
from schemas import ProjectCreate, ProjectDetail, ProjectOut
from services import project_service

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: Session = Depends(get_db),
                   user: User = Depends(require_manager_or_admin)):
    """Create a project for the signed-in manager or admin."""
    return project_service.create_project(data, user, db)


@router.get("", response_model=list[ProjectOut])
def list_projects(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                  db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Return a page of projects to any signed-in user."""
    return project_service.list_projects(skip, limit, db)


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    """Return project information and task counts by status."""
    return project_service.get_project(project_id, db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    """Delete a project; only an admin is allowed to do this."""
    project_service.delete_project(project_id, user, db)
