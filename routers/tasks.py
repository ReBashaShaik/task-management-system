"""HTTP endpoints for creating, reading, and updating tasks."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db, require_manager_or_admin
from models import User
from schemas import Priority, Status, TaskCreate, TaskOut, TaskStatusUpdate, TaskUpdate
from services import task_service

router = APIRouter(tags=["Tasks"])


@router.post("/projects/{project_id}/tasks", response_model=TaskOut,
             status_code=status.HTTP_201_CREATED)
def create_task(project_id: int, data: TaskCreate, db: Session = Depends(get_db),
                user: User = Depends(require_manager_or_admin)):
    """Create a task in a project and assign it to a team member."""
    return task_service.create_task(project_id, data, user, db)


@router.get("/projects/{project_id}/tasks", response_model=list[TaskOut])
def list_project_tasks(project_id: int, task_status: Status | None = Query(None, alias="status"),
                       priority: Priority | None = None, assignee_id: int | None = None,
                       db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """List project tasks and apply any requested filters."""
    return task_service.list_project_tasks(project_id, user, db, task_status, priority, assignee_id)


@router.get("/my/tasks", response_model=list[TaskOut])
def my_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Show the signed-in user's assigned tasks."""
    return task_service.list_my_tasks(user, db)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    """Show a task only to a user with access to it."""
    return task_service.get_task(task_id, user, db)


@router.patch("/tasks/{task_id}/status", response_model=TaskOut)
def update_task_status(task_id: int, data: TaskStatusUpdate, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    """Let the task's assignee move its status to the next step."""
    return task_service.update_task_status(task_id, data.status, user, db)


@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db),
                user: User = Depends(require_manager_or_admin)):
    """Update task details as its manager or an admin."""
    return task_service.update_task(task_id, data, user, db)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db),
                user: User = Depends(require_manager_or_admin)):
    """Delete a task as its manager or an admin."""
    task_service.delete_task(task_id, user, db)
