from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.task import TaskEntity
from app.domain.task_types import TaskPriority, TaskStatus
from app.domain.user import UserEntity
from app.domain.user_types import UserRole


@dataclass
class UserDTO:
    username: str
    role: UserRole


@dataclass
class TaskDTO:
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime


def user_to_entity(user: UserDTO) -> UserEntity:
    return UserEntity(username=user.username, role=user.role)


def task_to_entity(task: TaskDTO) -> TaskEntity:
    return TaskEntity(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
