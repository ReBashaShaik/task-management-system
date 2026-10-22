"""Add, list, and delete comments attached to tasks."""
from sqlalchemy.orm import Session

from models import Comment, Task, User
from schemas import CommentCreate
from services.errors import ForbiddenError, NotFoundError


def add_comment(task_id: int, data: CommentCreate, user: User, db: Session) -> Comment:
    """Save a comment with the signed-in user as its author."""
    if not db.get(Task, task_id):
        raise NotFoundError("Task not found")
    comment = Comment(task_id=task_id, author_id=user.id, content=data.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(task_id: int, db: Session) -> list[Comment]:
    """Return comments in the order they were created."""
    if not db.get(Task, task_id):
        raise NotFoundError("Task not found")
    return db.query(Comment).filter(Comment.task_id == task_id).order_by(Comment.id).all()


def delete_comment(comment_id: int, user: User, db: Session) -> None:
    """Allow an author or admin to remove a comment."""
    comment = db.get(Comment, comment_id)
    if not comment:
        raise NotFoundError("Comment not found")
    if user.role != "admin" and comment.author_id != user.id:
        raise ForbiddenError("Only the comment author or an admin can delete it")
    db.delete(comment)
    db.commit()
