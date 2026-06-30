from collections.abc import Generator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from tests.performance.conftest import TASK_COUNT
from tests.performance.timing import (
    MAX_MEDIAN_MS,
    MAX_P95_MS,
    format_latency_failure,
    get_tasks,
    measure_get_tasks_latency,
)

MAX_LIST_QUERIES = 5


@contextmanager
def count_sql_queries(engine: Engine) -> Generator[dict[str, int], None, None]:
    counter = {"count": 0}

    def before_cursor_execute(
        _conn,
        _cursor,
        _statement,
        _parameters,
        _context,
        _executemany,
    ) -> None:
        counter["count"] += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield counter
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


class TestTasksListPerformance:
    def test_get_tasks_responds_within_threshold(
        self,
        tasks_list_benchmark: dict[str, object],
    ) -> None:
        client = tasks_list_benchmark["client"]
        headers = tasks_list_benchmark["headers"]
        assert isinstance(client, TestClient)
        assert isinstance(headers, dict)

        measurement, payload = measure_get_tasks_latency(client, headers)

        assert len(payload) == TASK_COUNT
        assert measurement.median_ms < MAX_MEDIAN_MS, format_latency_failure(
            measurement,
            median_limit_ms=MAX_MEDIAN_MS,
            p95_limit_ms=MAX_P95_MS,
        )
        assert measurement.p95_ms < MAX_P95_MS, format_latency_failure(
            measurement,
            median_limit_ms=MAX_MEDIAN_MS,
            p95_limit_ms=MAX_P95_MS,
        )

    def test_get_tasks_avoids_n_plus_one_queries(
        self,
        tasks_list_benchmark: dict[str, object],
        engine: Engine,
    ) -> None:
        client = tasks_list_benchmark["client"]
        headers = tasks_list_benchmark["headers"]
        assert isinstance(client, TestClient)
        assert isinstance(headers, dict)

        with count_sql_queries(engine) as counter:
            payload = get_tasks(client, headers)

        assert len(payload) == TASK_COUNT
        assert counter["count"] <= MAX_LIST_QUERIES, (
            f"Expected at most {MAX_LIST_QUERIES} SQL queries, got {counter['count']}"
        )
        assert counter["count"] < TASK_COUNT, (
            "Query count scales with task rows — possible N+1 in list path"
        )
