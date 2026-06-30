from app.domain.mappers import TaskDTO, UserDTO, task_to_entity, user_to_entity
from app.domain.task import TaskEntity
from app.domain.user import UserEntity
from app.domain.user_types import UserRole
from app.models.task import Task
from app.models.user import User


def user_to_dto(user: User) -> UserDTO:
    return UserDTO(
        username=user.username,
        role=UserRole(user.role.value),
    )


def task_to_dto(task: Task) -> TaskDTO:
    return TaskDTO(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def user_model_to_entity(user: User) -> UserEntity:
    return user_to_entity(user_to_dto(user))


def task_model_to_entity(task: Task) -> TaskEntity:
    return task_to_entity(task_to_dto(task))
