from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPair(Token):
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ProjectCreate(ProjectBase):
    """Create a new project"""


class ProjectRead(ProjectBase):
    """Read a project"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ProjectWithTasks(ProjectRead):
    tasks: list[TaskRead] = []


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)


class TaskCreate(TaskBase):
    """Create a new task"""

    project_id: int | None = None


class TaskUpdate(BaseModel):
    """Update a task"""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    is_done: bool | None = None
    project_id: int | None = None


class TaskRead(TaskBase):
    """Read a task"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_done: bool
    created_at: datetime
    project: ProjectRead | None = None
