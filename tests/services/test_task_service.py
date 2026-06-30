from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import (
    InvalidStatusTransitionError,
    PermissionDeniedError,
    TaskCompletedError,
    TaskNotFoundError,
)
from app.domain.task_types import TaskPriority, TaskStatus
from app.domain.user import UserEntity
from app.domain.user_types import UserRole
from app.services.task_service import TaskService


def _task_model(
    *,
    task_id: int = 1,
    title: str = "Test task",
    description: str | None = None,
    status: TaskStatus = TaskStatus.NEW,
    priority: TaskPriority = TaskPriority.NORMAL,
) -> SimpleNamespace:
    now = datetime(2024, 1, 1, 12, 0, 0)
    return SimpleNamespace(
        id=task_id,
        title=title,
        description=description,
        status=status,
        priority=priority,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def task_service() -> TaskService:
    service = TaskService(MagicMock())
    service.repository = MagicMock()
    return service


@pytest.fixture
def admin_user() -> UserEntity:
    return UserEntity(username="admin", role=UserRole.ADMIN)


@pytest.fixture
def regular_user() -> UserEntity:
    return UserEntity(username="user", role=UserRole.USER)


class TestCreateTask:
    def test_rejects_non_new_initial_status(self, task_service: TaskService) -> None:
        with pytest.raises(InvalidStatusTransitionError):
            task_service.create_task(
                title="Task",
                description=None,
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.NORMAL,
            )

        task_service.repository.create.assert_not_called()
        task_service.db.commit.assert_not_called()

    def test_creates_task_with_new_status(self, task_service: TaskService) -> None:
        created = _task_model(title="Task", priority=TaskPriority.HIGH)
        task_service.repository.create.return_value = created

        result = task_service.create_task(
            title="Task",
            description="Details",
            status=TaskStatus.NEW,
            priority=TaskPriority.HIGH,
        )

        task_service.repository.create.assert_called_once_with(
            title="Task",
            description="Details",
            status=TaskStatus.NEW,
            priority=TaskPriority.HIGH,
        )
        task_service.db.commit.assert_called_once()
        assert result.status == TaskStatus.NEW
        assert result.priority == TaskPriority.HIGH

    def test_rolls_back_when_commit_fails(self, task_service: TaskService) -> None:
        task_service.db.commit.side_effect = RuntimeError("commit failed")

        with pytest.raises(RuntimeError, match="commit failed"):
            task_service._commit()

        task_service.db.rollback.assert_called_once()


class TestUpdateTask:
    def test_rejects_updates_to_completed_task(self, task_service: TaskService) -> None:
        task_service.repository.get.return_value = _task_model(status=TaskStatus.DONE)

        with pytest.raises(TaskCompletedError):
            task_service.update_task(1, title="Updated title")

        task_service.repository.update.assert_not_called()
        task_service.db.commit.assert_not_called()

    def test_rejects_invalid_status_transition(self, task_service: TaskService) -> None:
        task_service.repository.get.return_value = _task_model(status=TaskStatus.NEW)

        with pytest.raises(InvalidStatusTransitionError):
            task_service.update_task(1, status=TaskStatus.DONE)

        task_service.repository.update.assert_not_called()
        task_service.db.commit.assert_not_called()

    def test_allows_valid_status_transition(self, task_service: TaskService) -> None:
        current = _task_model(status=TaskStatus.NEW)
        updated = _task_model(status=TaskStatus.IN_PROGRESS)
        task_service.repository.get.return_value = current
        task_service.repository.update.return_value = updated

        result = task_service.update_task(1, status=TaskStatus.IN_PROGRESS)

        task_service.repository.update.assert_called_once_with(1, status=TaskStatus.IN_PROGRESS)
        task_service.db.commit.assert_called_once()
        assert result.status == TaskStatus.IN_PROGRESS

    def test_returns_existing_task_when_update_payload_is_empty(
        self,
        task_service: TaskService,
    ) -> None:
        current = _task_model(title="Unchanged")
        task_service.repository.get.return_value = current

        result = task_service.update_task(1)

        task_service.repository.update.assert_not_called()
        task_service.db.commit.assert_not_called()
        assert result.title == "Unchanged"

    def test_raises_when_repository_update_returns_none(self, task_service: TaskService) -> None:
        task_service.repository.get.return_value = _task_model(status=TaskStatus.NEW)
        task_service.repository.update.return_value = None

        with pytest.raises(TaskNotFoundError, match="Task not found"):
            task_service.update_task(1, title="Updated title")

        task_service.db.rollback.assert_called()

    def test_raises_when_task_not_found(self, task_service: TaskService) -> None:
        task_service.repository.get.return_value = None

        with pytest.raises(TaskNotFoundError):
            task_service.update_task(99, title="Updated title")


class TestDeleteTask:
    def test_requires_admin_role(self, task_service: TaskService, regular_user: UserEntity) -> None:
        with pytest.raises(PermissionDeniedError, match="Only admin users can delete tasks"):
            task_service.delete_task(1, regular_user)

        task_service.repository.get.assert_not_called()
        task_service.db.commit.assert_not_called()

    def test_admin_can_delete_completed_task(
        self,
        task_service: TaskService,
        admin_user: UserEntity,
    ) -> None:
        task_service.repository.get.return_value = _task_model(status=TaskStatus.DONE)
        task_service.repository.delete.return_value = True

        task_service.delete_task(1, admin_user)

        task_service.repository.delete.assert_called_once_with(1)
        task_service.db.commit.assert_called_once()

    def test_raises_when_task_not_found(
        self, task_service: TaskService, admin_user: UserEntity
    ) -> None:
        task_service.repository.get.return_value = None

        with pytest.raises(TaskNotFoundError):
            task_service.delete_task(1, admin_user)

        task_service.repository.delete.assert_not_called()

    def test_raises_when_delete_returns_false(
        self,
        task_service: TaskService,
        admin_user: UserEntity,
    ) -> None:
        task_service.repository.get.return_value = _task_model(status=TaskStatus.NEW)
        task_service.repository.delete.return_value = False

        with pytest.raises(TaskNotFoundError, match="Task not found"):
            task_service.delete_task(1, admin_user)

        task_service.db.commit.assert_not_called()
