from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from app.models.task import TaskStatus

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    position: Optional[int] = 0

    @field_validator("due_date", mode="before")
    @classmethod
    def parse_empty_string_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    position: Optional[int] = None

    @field_validator("due_date", mode="before")
    @classmethod
    def parse_empty_string_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v

class Task(TaskBase):
    id: UUID
    status: TaskStatus
    user_id: UUID
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
