import pytest

from app.core.exceptions import InvalidStatusTransitionError, TaskCompletedError
from app.domain.task_status import (
    validate_initial_status,
    validate_status_transition,
    validate_task_deletable,
    validate_task_modifiable,
)
from app.domain.task_types import TaskStatus


class TestStatusTransitions:
    @pytest.mark.parametrize(
        "current,target",
        [
            (TaskStatus.NEW, TaskStatus.NEW),
            (TaskStatus.IN_PROGRESS, TaskStatus.IN_PROGRESS),
            (TaskStatus.DONE, TaskStatus.DONE),
            (TaskStatus.NEW, TaskStatus.IN_PROGRESS),
            (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
        ],
    )
    def test_allows_valid_transitions(self, current: TaskStatus, target: TaskStatus) -> None:
        validate_status_transition(current, target)

    @pytest.mark.parametrize(
        "current,target",
        [
            (TaskStatus.NEW, TaskStatus.DONE),
            (TaskStatus.IN_PROGRESS, TaskStatus.NEW),
        ],
    )
    def test_rejects_invalid_transitions(self, current: TaskStatus, target: TaskStatus) -> None:
        with pytest.raises(InvalidStatusTransitionError):
            validate_status_transition(current, target)

    @pytest.mark.parametrize(
        "target",
        [TaskStatus.IN_PROGRESS, TaskStatus.NEW],
    )
    def test_rejects_transitions_from_done(self, target: TaskStatus) -> None:
        with pytest.raises(TaskCompletedError, match="Cannot revert status from done"):
            validate_status_transition(TaskStatus.DONE, target)


class TestInitialStatus:
    def test_accepts_new_status(self) -> None:
        validate_initial_status(TaskStatus.NEW)

    @pytest.mark.parametrize("status", [TaskStatus.IN_PROGRESS, TaskStatus.DONE])
    def test_rejects_non_new_status(self, status: TaskStatus) -> None:
        with pytest.raises(InvalidStatusTransitionError, match="New tasks must start"):
            validate_initial_status(status)


class TestCompletedTaskRestrictions:
    @pytest.mark.parametrize("status", [TaskStatus.NEW, TaskStatus.IN_PROGRESS])
    def test_allows_modifying_non_completed_tasks(self, status: TaskStatus) -> None:
        validate_task_modifiable(status)

    def test_rejects_modifying_completed_task(self) -> None:
        with pytest.raises(TaskCompletedError, match="Cannot edit a completed task"):
            validate_task_modifiable(TaskStatus.DONE)


class TestDeleteRestrictions:
    @pytest.mark.parametrize("status", [TaskStatus.NEW, TaskStatus.IN_PROGRESS, TaskStatus.DONE])
    def test_allows_admin_to_delete_any_status(self, status: TaskStatus) -> None:
        validate_task_deletable(status, is_admin=True)

    @pytest.mark.parametrize("status", [TaskStatus.NEW, TaskStatus.IN_PROGRESS])
    def test_allows_non_admin_to_delete_non_completed_tasks(self, status: TaskStatus) -> None:
        validate_task_deletable(status, is_admin=False)

    def test_rejects_non_admin_deleting_completed_task(self) -> None:
        with pytest.raises(TaskCompletedError, match="Cannot delete a completed task"):
            validate_task_deletable(TaskStatus.DONE, is_admin=False)
