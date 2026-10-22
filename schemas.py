"""Pydantic shapes define what the API accepts and returns."""
from datetime import date, datetime
from typing import Annotated, Literal
from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Role = Literal["member", "project_manager", "admin"]
Status = Literal["todo", "in_progress", "review", "done"]
Priority = Literal["low", "medium", "high", "critical"]


def require_gmail_address(email: str) -> str:
    """Allow a valid email address only when its domain is gmail.com."""
    if email.rsplit("@", 1)[-1].lower() != "gmail.com":
        raise ValueError("Email must end with @gmail.com")
    return email


GmailEmail = Annotated[EmailStr, AfterValidator(require_gmail_address)]


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: GmailEmail
    password: str = Field(min_length=8, max_length=72)
    role: Literal["member", "project_manager"] = "member"

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        """Remove extra spaces and reject a name made only of spaces."""
        clean_name = value.strip()
        if not clean_name:
            raise ValueError("Name cannot be empty")
        return clean_name


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Role
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str | None = None


class ProjectOut(BaseModel):
    id: int
    manager_id: int
    name: str
    description: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProjectDetail(ProjectOut):
    task_summary: dict[str, int]


class TaskCreate(BaseModel):
    assignee_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: Priority = "medium"
    due_date: date | None = None


class TaskUpdate(BaseModel):
    assignee_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: Priority | None = None
    due_date: date | None = None

    @model_validator(mode="before")
    @classmethod
    def check_update_fields(cls, values):
        """Require at least one change and reject null for required task fields."""
        if not isinstance(values, dict) or not values:
            raise ValueError("Provide at least one task field to update")

        required_values = {"assignee_id", "title", "priority"}
        for field_name in required_values:
            if field_name in values and values[field_name] is None:
                raise ValueError(f"{field_name} cannot be null")

        return values


class TaskStatusUpdate(BaseModel):
    status: Status


class TaskOut(BaseModel):
    id: int
    project_id: int
    assignee_id: int
    title: str
    description: str | None
    status: Status
    priority: Priority
    due_date: date | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentOut(BaseModel):
    id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
