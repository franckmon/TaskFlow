import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.task_types import TaskPriority, TaskStatus
from app.repositories.task_repository import TaskRepository
from tests.performance.timing import WARMUP_RUNS, warm_up_get_tasks

TASK_COUNT = 100


@pytest.fixture
def hundred_tasks(db_session: Session) -> None:
    """Seed tasks during fixture setup — never inside latency measurement."""
    repository = TaskRepository(db_session)
    for index in range(TASK_COUNT):
        repository.create(
            title=f"Performance task {index:03d}",
            description=f"Load test description {index}",
            status=TaskStatus.NEW,
            priority=TaskPriority.NORMAL,
        )


@pytest.fixture
def tasks_list_benchmark(
    client: TestClient,
    admin_headers: dict[str, str],
    hundred_tasks: None,
) -> dict[str, object]:
    """
    Prepare a warm task-list endpoint before tests measure latency or queries.

    Runs after DB seeding and auth setup; warm-up requests sit outside assertions.
    """
    warm_up_get_tasks(client, admin_headers, runs=WARMUP_RUNS)
    return {
        "client": client,
        "headers": admin_headers,
        "task_count": TASK_COUNT,
    }
