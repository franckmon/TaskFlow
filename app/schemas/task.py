from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.task_types import (
    DESCRIPTION_MAX_LENGTH,
    SortOrder,
    TaskPriority,
    TaskSortField,
    TaskStatus,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
)

SEARCH_MAX_LENGTH = 120

_TASK_EXAMPLE = {
    "id": 1,
    "title": "Deploy release",
    "description": "Roll out v1.0 to production",
    "status": "new",
    "priority": "high",
    "created_at": "2026-06-29T12:00:00",
    "updated_at": "2026-06-29T12:00:00",
}


class TaskBase(BaseModel):
    """Shared task fields."""

    title: str = Field(
        ...,
        min_length=TITLE_MIN_LENGTH,
        max_length=TITLE_MAX_LENGTH,
        description=f"Task title ({TITLE_MIN_LENGTH}–{TITLE_MAX_LENGTH} characters)",
        examples=["Deploy release"],
    )
    description: Optional[str] = Field(
        None,
        max_length=DESCRIPTION_MAX_LENGTH,
        description=f"Optional description (max {DESCRIPTION_MAX_LENGTH} characters)",
        examples=["Roll out v1.0 to production"],
    )
    status: TaskStatus = Field(
        default=TaskStatus.NEW,
        description="Current lifecycle status",
        examples=["new"],
    )
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL,
        description="Relative priority",
        examples=["high"],
    )


class TaskCreate(TaskBase):
    """Request body for creating a task. New tasks must use status `new`."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Deploy release",
                    "description": "Roll out v1.0 to production",
                    "status": "new",
                    "priority": "high",
                }
            ]
        }
    )


class TaskUpdate(BaseModel):
    """Partial update; only provided fields are changed."""

    title: Optional[str] = Field(
        None,
        min_length=TITLE_MIN_LENGTH,
        max_length=TITLE_MAX_LENGTH,
        description=f"New title ({TITLE_MIN_LENGTH}–{TITLE_MAX_LENGTH} characters)",
    )
    description: Optional[str] = Field(
        None,
        max_length=DESCRIPTION_MAX_LENGTH,
        description=f"New description (max {DESCRIPTION_MAX_LENGTH} characters)",
    )
    status: Optional[TaskStatus] = Field(
        None,
        description="New status (forward-only: new → in_progress → done)",
    )
    priority: Optional[TaskPriority] = Field(None, description="New priority")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "in_progress"},
                {"title": "Deploy release (updated)", "priority": "normal"},
            ]
        }
    )


class TaskResponse(TaskBase):
    """Task returned by the API."""

    id: int = Field(..., description="Task primary key", examples=[1])
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [_TASK_EXAMPLE]},
    )


class TaskListQuery(BaseModel):
    """Query parameters for listing tasks."""

    skip: int = Field(default=0, ge=0, description="Number of records to skip", examples=[0])
    limit: int = Field(
        default=100,
        ge=1,
        le=100,
        description="Maximum records to return",
        examples=[20],
    )
    status: Optional[TaskStatus] = Field(None, description="Filter by status")
    priority: Optional[TaskPriority] = Field(None, description="Filter by priority")
    search: Optional[str] = Field(
        default=None,
        max_length=SEARCH_MAX_LENGTH,
        description=f"Case-insensitive search in title and description (max {SEARCH_MAX_LENGTH} chars)",
        examples=["release"],
    )
    sort_by: TaskSortField = Field(
        default=TaskSortField.CREATED_AT,
        description="Field used for ordering",
    )
    sort_order: SortOrder = Field(
        default=SortOrder.DESC,
        description="Sort direction",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "new",
                    "priority": "high",
                    "search": "release",
                    "sort_by": "created_at",
                    "sort_order": "desc",
                    "skip": 0,
                    "limit": 20,
                }
            ]
        }
    )

    @field_validator("search", mode="before")
    @classmethod
    def normalize_search(cls, value: object) -> Optional[str]:
        # Blank query params mean no filter; whitespace-only strings are rejected.
        if value is None or value == "":
            return None

        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized:
            raise ValueError("search cannot be empty")

        return normalized

    @field_validator("search")
    @classmethod
    def validate_search_length(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value) > SEARCH_MAX_LENGTH:
            raise ValueError(f"search must be at most {SEARCH_MAX_LENGTH} characters")
        return value
