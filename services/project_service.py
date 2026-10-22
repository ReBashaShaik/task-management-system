"""Create, find, summarize, and delete projects."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Project, Task, User
from schemas import ProjectCreate, ProjectDetail
from services.errors import ForbiddenError, NotFoundError


def create_project(data: ProjectCreate, manager: User, db: Session) -> Project:
    """Save a project under the signed-in manager."""
    project = Project(manager_id=manager.id, name=data.name, description=data.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(skip: int, limit: int, db: Session) -> list[Project]:
    """Return one page of projects in a stable order."""
    return db.query(Project).order_by(Project.id).offset(skip).limit(limit).all()


def get_project(project_id: int, db: Session) -> ProjectDetail:
    """Return project details and the number of tasks in each status."""
    project = db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")

    counts = dict(
        db.query(Task.status, func.count(Task.id))
        .filter(Task.project_id == project_id)
        .group_by(Task.status)
        .all()
    )
    summary = {status: counts.get(status, 0) for status in ("todo", "in_progress", "review", "done")}
    return ProjectDetail(
        id=project.id,
        manager_id=project.manager_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        task_summary=summary,
    )


def delete_project(project_id: int, user: User, db: Session) -> None:
    """Only an admin can delete a project; related tasks/comments cascade."""
    if user.role != "admin":
        raise ForbiddenError("You cannot delete this project. Only an admin can delete projects.")
    project = db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")
    db.delete(project)
    db.commit()
