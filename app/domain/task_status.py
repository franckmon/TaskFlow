from app.core.exceptions import InvalidStatusTransitionError, TaskCompletedError
from app.domain.task_types import TaskStatus

ALLOWED_STATUS_TRANSITIONS: dict[TaskStatus, TaskStatus] = {
    TaskStatus.NEW: TaskStatus.IN_PROGRESS,
    TaskStatus.IN_PROGRESS: TaskStatus.DONE,
}

TERMINAL_STATUSES: frozenset[TaskStatus] = frozenset({TaskStatus.DONE})


def validate_status_transition(current: TaskStatus, target: TaskStatus) -> None:
    if current == target:
        return

    if current in TERMINAL_STATUSES:
        raise TaskCompletedError("Cannot revert status from done")

    allowed_target = ALLOWED_STATUS_TRANSITIONS.get(current)
    if allowed_target != target:
        raise InvalidStatusTransitionError(
            f"Invalid status transition from '{current.value}' to '{target.value}'"
        )


def validate_task_modifiable(status: TaskStatus) -> None:
    if status in TERMINAL_STATUSES:
        raise TaskCompletedError("Cannot edit a completed task")


def validate_task_deletable(status: TaskStatus, *, is_admin: bool = False) -> None:
    # Non-admins cannot delete completed tasks; admins may delete any task.
    if status in TERMINAL_STATUSES and not is_admin:
        raise TaskCompletedError("Cannot delete a completed task")


def validate_initial_status(status: TaskStatus) -> None:
    if status != TaskStatus.NEW:
        raise InvalidStatusTransitionError(
            f"New tasks must start with status '{TaskStatus.NEW.value}'"
        )
