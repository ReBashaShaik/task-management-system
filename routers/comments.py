"""HTTP endpoints for comments attached to tasks."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dependencies import get_current_user, get_db
from models import User
from schemas import CommentCreate, CommentOut
from services import comment_service

router = APIRouter(tags=["Comments"])


@router.post("/tasks/{task_id}/comments", response_model=CommentOut,
             status_code=status.HTTP_201_CREATED)
def add_comment(task_id: int, data: CommentCreate, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    """Add a comment, saving the signed-in user as its author."""
    return comment_service.add_comment(task_id, data, user, db)


@router.get("/tasks/{task_id}/comments", response_model=list[CommentOut])
def list_comments(task_id: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    """List comments for a task."""
    return comment_service.list_comments(task_id, db)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    """Let the author or an admin delete a comment."""
    comment_service.delete_comment(comment_id, user, db)
