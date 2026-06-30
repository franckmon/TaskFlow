from datetime import datetime

import pytest

from app.domain.task_types import TaskPriority, TaskSortField, SortOrder, TaskStatus
from app.repositories.task_repository import TaskRepository


def create_task(
    repository: TaskRepository,
    *,
    title: str = "Task",
    description: str | None = None,
    status: TaskStatus = TaskStatus.NEW,
    priority: TaskPriority = TaskPriority.NORMAL,
    created_at: datetime | None = None,
) -> None:
    kwargs = {
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
    }
    if created_at is not None:
        kwargs["created_at"] = created_at
        kwargs["updated_at"] = created_at

    repository.create(**kwargs)


class TestCreate:
    def test_create_persists_task(self, task_repository: TaskRepository) -> None:
        created = task_repository.create(
            title="New task",
            description="Details",
            status=TaskStatus.NEW,
            priority=TaskPriority.HIGH,
        )

        assert created.id is not None
        assert created.title == "New task"
        assert created.description == "Details"
        assert created.status == TaskStatus.NEW
        assert created.priority == TaskPriority.HIGH

        stored = task_repository.get(created.id)
        assert stored is not None
        assert stored.title == "New task"


class TestRead:
    def test_get_returns_none_for_missing_task(self, task_repository: TaskRepository) -> None:
        assert task_repository.get(999) is None

    def test_get_by_title(self, task_repository: TaskRepository) -> None:
        task_repository.create(
            title="Unique title",
            description=None,
            status=TaskStatus.NEW,
            priority=TaskPriority.NORMAL,
        )

        found = task_repository.get_by_title("Unique title")

        assert found is not None
        assert found.title == "Unique title"

    def test_get_all_applies_pagination(self, task_repository: TaskRepository) -> None:
        for index in range(5):
            create_task(task_repository, title=f"Task {index}")

        page = task_repository.get_all(skip=2, limit=2)

        assert len(page) == 2
        assert [task.title for task in page] == ["Task 2", "Task 3"]


class TestUpdate:
    def test_update_changes_fields(self, task_repository: TaskRepository) -> None:
        created = task_repository.create(
            title="Original",
            description="Old description",
            status=TaskStatus.NEW,
            priority=TaskPriority.LOW,
        )

        updated = task_repository.update(
            created.id,
            title="Updated",
            description="New description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
        )

        assert updated is not None
        assert updated.title == "Updated"
        assert updated.description == "New description"
        assert updated.status == TaskStatus.IN_PROGRESS
        assert updated.priority == TaskPriority.HIGH

        stored = task_repository.get(created.id)
        assert stored is not None
        assert stored.title == "Updated"

    def test_update_returns_none_for_missing_task(self, task_repository: TaskRepository) -> None:
        assert task_repository.update(999, title="Missing") is None


class TestDelete:
    def test_delete_removes_task(self, task_repository: TaskRepository) -> None:
        created = task_repository.create(
            title="To delete",
            description=None,
            status=TaskStatus.NEW,
            priority=TaskPriority.NORMAL,
        )

        deleted = task_repository.delete(created.id)

        assert deleted is True
        assert task_repository.get(created.id) is None

    def test_delete_returns_false_for_missing_task(self, task_repository: TaskRepository) -> None:
        assert task_repository.delete(999) is False


class TestFilter:
    def test_filter_by_status(self, task_repository: TaskRepository) -> None:
        create_task(task_repository, title="New task", status=TaskStatus.NEW)
        create_task(task_repository, title="Done task", status=TaskStatus.DONE)

        results = task_repository.filter(status=TaskStatus.DONE)

        assert len(results) == 1
        assert results[0].title == "Done task"

    def test_filter_by_priority(self, task_repository: TaskRepository) -> None:
        create_task(task_repository, title="Low task", priority=TaskPriority.LOW)
        create_task(task_repository, title="High task", priority=TaskPriority.HIGH)

        results = task_repository.filter(priority=TaskPriority.HIGH)

        assert len(results) == 1
        assert results[0].title == "High task"

    def test_filter_by_status_and_priority(self, task_repository: TaskRepository) -> None:
        create_task(
            task_repository,
            title="Match",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
        )
        create_task(
            task_repository,
            title="Wrong status",
            status=TaskStatus.NEW,
            priority=TaskPriority.HIGH,
        )
        create_task(
            task_repository,
            title="Wrong priority",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.LOW,
        )

        results = task_repository.filter(
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
        )

        assert len(results) == 1
        assert results[0].title == "Match"


class TestSearch:
    def test_search_matches_title(self, task_repository: TaskRepository) -> None:
        create_task(task_repository, title="Deploy release", description="ops")
        create_task(task_repository, title="Write docs", description="docs")

        results = task_repository.filter(search="deploy")

        assert len(results) == 1
        assert results[0].title == "Deploy release"

    def test_search_matches_description(self, task_repository: TaskRepository) -> None:
        create_task(task_repository, title="Task A", description="billing integration")
        create_task(task_repository, title="Task B", description="unrelated")

        results = task_repository.filter(search="billing")

        assert len(results) == 1
        assert results[0].title == "Task A"


class TestSorting:
    @pytest.mark.parametrize(
        ("sort_order", "expected_titles"),
        [
            (SortOrder.ASC, ["Older", "Middle", "Newer"]),
            (SortOrder.DESC, ["Newer", "Middle", "Older"]),
        ],
    )
    def test_sort_by_created_at(
        self,
        task_repository: TaskRepository,
        sort_order: SortOrder,
        expected_titles: list[str],
    ) -> None:
        create_task(
            task_repository,
            title="Older",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
        )
        create_task(
            task_repository,
            title="Middle",
            created_at=datetime(2024, 1, 2, 10, 0, 0),
        )
        create_task(
            task_repository,
            title="Newer",
            created_at=datetime(2024, 1, 3, 10, 0, 0),
        )

        results = task_repository.filter(
            sort_by=TaskSortField.CREATED_AT,
            sort_order=sort_order,
        )

        assert [task.title for task in results] == expected_titles

    @pytest.mark.parametrize(
        ("sort_order", "expected_titles"),
        [
            (SortOrder.ASC, ["High task", "Low task", "Normal task"]),
            (SortOrder.DESC, ["Normal task", "Low task", "High task"]),
        ],
    )
    def test_sort_by_priority(
        self,
        task_repository: TaskRepository,
        sort_order: SortOrder,
        expected_titles: list[str],
    ) -> None:
        create_task(task_repository, title="High task", priority=TaskPriority.HIGH)
        create_task(task_repository, title="Low task", priority=TaskPriority.LOW)
        create_task(task_repository, title="Normal task", priority=TaskPriority.NORMAL)

        results = task_repository.filter(
            sort_by=TaskSortField.PRIORITY,
            sort_order=sort_order,
        )

        assert [task.title for task in results] == expected_titles


class TestFilterPagination:
    def test_filter_applies_skip_and_limit(self, task_repository: TaskRepository) -> None:
        for index in range(5):
            create_task(
                task_repository,
                title=f"Task {index}",
                created_at=datetime(2024, 1, index + 1, 10, 0, 0),
            )

        results = task_repository.filter(
            sort_by=TaskSortField.CREATED_AT,
            sort_order=SortOrder.ASC,
            skip=1,
            limit=2,
        )

        assert len(results) == 2
        assert [task.title for task in results] == ["Task 1", "Task 2"]
