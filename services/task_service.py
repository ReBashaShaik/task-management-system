"""Apply project ownership, task assignment, filtering, and status rules."""
from sqlalchemy.orm import Session

from models import Project, Task, User
from schemas import TaskCreate, TaskUpdate
from services.errors import ForbiddenError, InvalidRequestError, NotFoundError

STATUS_FLOW = ("todo", "in_progress", "review", "done")
PRIORITIES = {"low", "medium", "high", "critical"}


def get_task_or_raise(task_id: int, db: Session) -> Task:
    """Find a task or return a clear not-found error."""
    task = db.get(Task, task_id)
    if not task:
        raise NotFoundError("Task not found")
    return task


def check_project_manager(user: User, project: Project) -> None:
    """Allow admins everywhere and managers only in their own projects."""
    if user.role != "admin" and project.manager_id != user.id:
        raise ForbiddenError("You can only manage tasks in your own projects")


def check_assignee(assignee_id: int, db: Session) -> None:
    """Tasks must be assigned to an active member account."""
    assignee = db.get(User, assignee_id)
    if not assignee or assignee.role != "member" or not assignee.is_active:
        raise InvalidRequestError("Assignee must be an active member")


def create_task(project_id: int, data: TaskCreate, user: User, db: Session) -> Task:
    """Create a task after checking project ownership and assignee role."""
    project = db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")
    check_project_manager(user, project)
    check_assignee(data.assignee_id, db)

    task = Task(project_id=project_id, **data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_project_tasks(project_id: int, user: User, db: Session,
                       task_status: str | None = None, priority: str | None = None,
                       assignee_id: int | None = None) -> list[Task]:
    """Apply filters and limit members to the tasks assigned to them."""
    project = db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")
    if user.role == "project_manager" and project.manager_id != user.id:
        raise ForbiddenError("You can only view your own projects")

    query = db.query(Task).filter(Task.project_id == project_id)
    if user.role == "member":
        query = query.filter(Task.assignee_id == user.id)
    if task_status:
        query = query.filter(Task.status == task_status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)
    return query.order_by(Task.id).all()


def list_my_tasks(user: User, db: Session) -> list[Task]:
    """Return only tasks assigned to the signed-in user."""
    return db.query(Task).filter(Task.assignee_id == user.id).order_by(Task.id).all()


def get_task(task_id: int, user: User, db: Session) -> Task:
    """Return a task only when this role is allowed to view it."""
    task = get_task_or_raise(task_id, db)
    if user.role == "project_manager":
        check_project_manager(user, task.project)
    elif user.role == "member" and task.assignee_id != user.id:
        raise NotFoundError("Task not found")
    return task


def update_task_status(task_id: int, new_status: str, user: User, db: Session) -> Task:
    """Let only the assignee move a task exactly one step forward."""
    task = get_task_or_raise(task_id, db)
    if task.assignee_id != user.id:
        raise ForbiddenError("Only the assigned member can update task status")

    current_index = STATUS_FLOW.index(task.status)
    if current_index == len(STATUS_FLOW) - 1 or STATUS_FLOW[current_index + 1] != new_status:
        raise InvalidRequestError("Move the task to the next status in order")
    task.status = new_status
    db.commit()
    db.refresh(task)
    return task


def update_task(task_id: int, data: TaskUpdate, user: User, db: Session) -> Task:
    """Change task details after checking the manager owns its project."""
    task = get_task_or_raise(task_id, db)
    check_project_manager(user, task.project)
    changes = data.model_dump(exclude_unset=True)
    if "assignee_id" in changes:
        check_assignee(changes["assignee_id"], db)
    for field_name, value in changes.items():
        setattr(task, field_name, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(task_id: int, user: User, db: Session) -> None:
    """Delete a task only for its project manager or an admin."""
    task = get_task_or_raise(task_id, db)
    check_project_manager(user, task.project)
    db.delete(task)
    db.commit()
