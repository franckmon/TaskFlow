from typing import List

import pytest
from fastapi.testclient import TestClient

from app.schemas.task import TaskResponse
from tests.api.conftest import create_task_via_api
from tests.api.contracts.helpers import assert_model_fields, assert_response_schema
from tests.api.test_errors import assert_error

TASK_RESPONSE_FIELDS = {
    "id",
    "title",
    "description",
    "status",
    "priority",
    "created_at",
    "updated_at",
}

LIST_PARAMS = {"sort_by": "created_at", "sort_order": "asc"}
PAGE_SIZE = 3
TASK_COUNT = 7


def list_tasks(
    client: TestClient,
    headers: dict[str, str],
    **params: object,
) -> list[TaskResponse]:
    response = client.get("/tasks/", headers=headers, params={**LIST_PARAMS, **params})
    tasks = assert_response_schema(response, List[TaskResponse])
    for task in tasks:
        assert_model_fields(task, TASK_RESPONSE_FIELDS)
    return tasks


@pytest.fixture
def pagination_tasks(
    client: TestClient,
    admin_headers: dict[str, str],
) -> list[dict]:
    return [
        create_task_via_api(client, admin_headers, title=f"Page task {index:02d}")
        for index in range(TASK_COUNT)
    ]


class TestPaginationValidation:
    @pytest.mark.parametrize("limit", [0, -1])
    def test_rejects_non_positive_limit(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        limit: int,
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"limit": limit})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="limit:",
        )

    def test_rejects_negative_skip(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"skip": -1})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="skip:",
        )

    def test_rejects_limit_above_schema_max(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"limit": 10_000})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="limit:",
        )


class TestPaginationSuccess:
    def test_empty_database_returns_empty_list(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        tasks = list_tasks(client, admin_headers)

        assert tasks == []

    def test_last_page_returns_remaining_items_without_off_by_one(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        pagination_tasks: list[dict],
    ) -> None:
        first_page = list_tasks(client, admin_headers, skip=0, limit=PAGE_SIZE)
        second_page = list_tasks(client, admin_headers, skip=PAGE_SIZE, limit=PAGE_SIZE)
        last_page = list_tasks(client, admin_headers, skip=6, limit=PAGE_SIZE)
        beyond_last = list_tasks(client, admin_headers, skip=7, limit=PAGE_SIZE)

        assert len(first_page) == PAGE_SIZE
        assert len(second_page) == PAGE_SIZE
        assert len(last_page) == 1
        assert len(beyond_last) == 0

        assert last_page[0].title == pagination_tasks[6]["title"]
        assert last_page[0].id == pagination_tasks[6]["id"]

    def test_paginated_slices_are_consistent_with_full_list(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        pagination_tasks: list[dict],
    ) -> None:
        full_list = list_tasks(client, admin_headers, limit=100)
        expected_ids = [task["id"] for task in pagination_tasks]

        assert [task.id for task in full_list] == expected_ids

        collected_ids: list[int] = []
        for skip in range(0, TASK_COUNT, PAGE_SIZE):
            page = list_tasks(client, admin_headers, skip=skip, limit=PAGE_SIZE)
            collected_ids.extend(task.id for task in page)

        assert collected_ids == expected_ids
        assert len(collected_ids) == len(set(collected_ids))

    def test_limit_at_schema_max_returns_all_tasks(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        pagination_tasks: list[dict],
    ) -> None:
        tasks = list_tasks(client, admin_headers, limit=100)

        assert len(tasks) == TASK_COUNT
        assert [task.id for task in tasks] == [task["id"] for task in pagination_tasks]
