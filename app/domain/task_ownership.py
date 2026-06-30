from dataclasses import dataclass
from typing import Any

from app.core.exceptions import PermissionDeniedError
from app.domain.user_types import UserRole

TASK_OWNERSHIP_SCOPE = "global_shared_workspace"


@dataclass(frozen=True, slots=True)
class TaskOwnershipContext:
    owner_id: int | str | None
    invalid_owner: bool = False


@dataclass(frozen=True, slots=True)
class UserOwnershipContext:
    id: int | str | None
    role: UserRole


def normalize_actor_id(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.lstrip("-").isdigit():
        return int(value)
    return None


def _task_owner_from_raw(value: Any) -> tuple[int | str | None, bool]:
    if value is None:
        return None, False
    if isinstance(value, bool):
        return None, True
    if isinstance(value, int):
        return value, False
    if isinstance(value, str):
        if value.lstrip("-").isdigit():
            return value, False
        return None, True
    return None, True


def is_task_access_allowed(
    user: UserOwnershipContext | None,
    task: TaskOwnershipContext,
) -> bool:
    if user is None:
        return False

    user_id = normalize_actor_id(user.id)
    if user_id is None:
        return False

    if user.role == UserRole.ADMIN:
        return True

    if task.invalid_owner:
        return False

    owner_id = normalize_actor_id(task.owner_id)
    if owner_id is None:
        return True

    return user_id == owner_id


def assert_task_access_allowed(
    user: UserOwnershipContext | None,
    task: TaskOwnershipContext,
) -> None:
    if not is_task_access_allowed(user, task):
        raise PermissionDeniedError("You do not have access to this task")


def user_ownership_context_from_mapping(user: Any) -> UserOwnershipContext | None:
    """Build user context from duck-typed objects."""
    if user is None:
        return None

    raw_role = getattr(user, "role", UserRole.USER)
    role = raw_role if isinstance(raw_role, UserRole) else UserRole.USER
    return UserOwnershipContext(id=getattr(user, "id", None), role=role)


def task_ownership_context_from_mapping(task: Any) -> TaskOwnershipContext:
    """Build task context from duck-typed objects."""
    raw_owner = getattr(task, "owner_id", None)
    owner_id, invalid_owner = _task_owner_from_raw(raw_owner)
    return TaskOwnershipContext(owner_id=owner_id, invalid_owner=invalid_owner)
