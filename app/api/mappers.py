from app.domain.auth import AuthResult
from app.domain.task import TaskEntity
from app.domain.user import UserEntity
from app.schemas.auth import TokenResponse, UserResponse
from app.schemas.task import TaskResponse


def task_to_response(entity: TaskEntity) -> TaskResponse:
    return TaskResponse(
        id=entity.id,
        title=entity.title,
        description=entity.description,
        status=entity.status,
        priority=entity.priority,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def user_to_response(entity: UserEntity) -> UserResponse:
    return UserResponse(username=entity.username, role=entity.role)


def auth_result_to_response(result: AuthResult) -> TokenResponse:
    return TokenResponse(
        access_token=result.access_token,
        role=result.role,
    )
