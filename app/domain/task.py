from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.task_types import TaskPriority, TaskStatus


@dataclass
class TaskEntity:
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
