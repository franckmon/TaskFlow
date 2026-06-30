from typing import List

from fastapi.testclient import TestClient

from app.schemas.auth import TokenResponse, UserResponse
from app.schemas.common import MessageResponse
from app.schemas.task import TaskResponse
from tests.api.conftest import create_task_via_api
from tests.api.contracts.helpers import assert_model_fields, assert_response_schema

TASK_RESPONSE_FIELDS = {
    "id",
    "title",
    "description",
    "status",
    "priority",
    "created_at",
    "updated_at",
}
TOKEN_RESPONSE_FIELDS = {"access_token", "token_type", "role"}
USER_RESPONSE_FIELDS = {"username", "role"}
MESSAGE_RESPONSE_FIELDS = {"message"}


class TestAuthEndpointContracts:
    def test_post_auth_login_response_contract(
        self,
        client: TestClient,
        seed_admin,
        admin_credentials: dict[str, str],
    ) -> None:
        response = client.post("/auth/login", json=admin_credentials)

        payload = assert_response_schema(response, TokenResponse)
        assert_model_fields(payload, TOKEN_RESPONSE_FIELDS)

    def test_get_auth_me_response_contract(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/auth/me", headers=admin_headers)

        payload = assert_response_schema(response, UserResponse)
        assert_model_fields(payload, USER_RESPONSE_FIELDS)


class TestTaskEndpointContracts:
    def test_get_tasks_response_contract(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        create_task_via_api(client, admin_headers, title="Contract list task")

        response = client.get("/tasks/", headers=admin_headers)

        tasks = assert_response_schema(response, List[TaskResponse])
        assert len(tasks) >= 1
        assert_model_fields(tasks[0], TASK_RESPONSE_FIELDS)

    def test_post_tasks_response_contract(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.post(
            "/tasks/",
            headers=admin_headers,
            json={
                "title": "Contract create task",
                "description": "Schema regression check",
                "status": "new",
                "priority": "normal",
            },
        )

        payload = assert_response_schema(response, TaskResponse)
        assert_model_fields(payload, TASK_RESPONSE_FIELDS)

    def test_put_tasks_id_response_contract(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        created = create_task_via_api(client, admin_headers, title="Contract update task")

        response = client.put(
            f"/tasks/{created['id']}",
            headers=admin_headers,
            json={"status": "in_progress"},
        )

        payload = assert_response_schema(response, TaskResponse)
        assert_model_fields(payload, TASK_RESPONSE_FIELDS)

    def test_delete_tasks_id_response_contract(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        created = create_task_via_api(client, admin_headers, title="Contract delete task")

        response = client.delete(f"/tasks/{created['id']}", headers=admin_headers)

        payload = assert_response_schema(response, MessageResponse)
        assert_model_fields(payload, MESSAGE_RESPONSE_FIELDS)
