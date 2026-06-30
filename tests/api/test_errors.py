import pytest
from fastapi.testclient import TestClient

from app.domain.task_types import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH
from tests.api.conftest import create_task_via_api


def assert_error(
    response,
    *,
    status_code: int,
    code: str,
    detail: str | None = None,
    detail_contains: str | None = None,
) -> None:
    assert response.status_code == status_code
    payload = response.json()
    assert payload["code"] == code
    if detail is not None:
        assert payload["detail"] == detail
    if detail_contains is not None:
        assert detail_contains in payload["detail"]


class TestUnauthorized401:
    def test_login_unknown_username_returns_401(self, client: TestClient, seed_admin) -> None:
        response = client.post(
            "/auth/login",
            json={"username": "missing-user", "password": "any-password"},
        )

        assert_error(
            response,
            status_code=401,
            code="invalid_credentials",
            detail="Incorrect username or password",
        )

    def test_invalid_bearer_token_returns_401(
        self,
        client: TestClient,
        seed_admin,
    ) -> None:
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert_error(
            response,
            status_code=401,
            code="unauthorized",
            detail="Invalid authentication credentials",
        )

    def test_token_for_deleted_user_returns_401(
        self,
        client: TestClient,
        seed_admin,
        admin_headers: dict[str, str],
        db_session,
    ) -> None:
        db_session.delete(seed_admin)
        db_session.flush()

        response = client.get("/auth/me", headers=admin_headers)

        assert_error(
            response,
            status_code=401,
            code="unauthorized",
            detail="User not found",
        )


class TestForbidden403:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("get", "/tasks/"),
            ("post", "/tasks/"),
            ("get", "/tasks/1"),
            ("put", "/tasks/1"),
            ("delete", "/tasks/1"),
        ],
    )
    def test_protected_task_endpoints_require_auth(
        self,
        client: TestClient,
        method: str,
        path: str,
    ) -> None:
        response = client.request(
            method, path, json={"title": "Task"} if method == "post" else None
        )

        assert response.status_code == 403
        assert response.json()["code"] == "permission_denied"


class TestNotFound404:
    def test_update_missing_task_returns_404(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.put(
            "/tasks/99999",
            headers=admin_headers,
            json={"title": "Missing task"},
        )

        assert_error(
            response,
            status_code=404,
            code="task_not_found",
            detail="Task not found",
        )

    def test_delete_missing_task_returns_404(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.delete("/tasks/99999", headers=admin_headers)

        assert_error(
            response,
            status_code=404,
            code="task_not_found",
            detail="Task not found",
        )


class TestBadRequest400:
    def test_update_reverts_in_progress_task_status(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        created = create_task_via_api(client, admin_headers, title="In progress task")
        client.put(f"/tasks/{created['id']}", headers=admin_headers, json={"status": "in_progress"})

        response = client.put(
            f"/tasks/{created['id']}",
            headers=admin_headers,
            json={"status": "new"},
        )

        assert_error(
            response,
            status_code=400,
            code="invalid_status_transition",
            detail="Invalid status transition from 'in_progress' to 'new'",
        )


class TestValidation422:
    def test_create_task_missing_title(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.post("/tasks/", headers=admin_headers, json={"description": "No title"})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="body.title",
        )

    def test_create_task_title_too_short(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.post(
            "/tasks/",
            headers=admin_headers,
            json={"title": "ab"},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains=f"at least {TITLE_MIN_LENGTH} characters",
        )

    def test_create_task_title_too_long(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.post(
            "/tasks/",
            headers=admin_headers,
            json={"title": "x" * (TITLE_MAX_LENGTH + 1)},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains=f"at most {TITLE_MAX_LENGTH} characters",
        )

    def test_create_task_description_too_long(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.post(
            "/tasks/",
            headers=admin_headers,
            json={
                "title": "Valid title",
                "description": "x" * (DESCRIPTION_MAX_LENGTH + 1),
            },
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains=f"at most {DESCRIPTION_MAX_LENGTH} characters",
        )

    def test_create_task_invalid_status_enum(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.post(
            "/tasks/",
            headers=admin_headers,
            json={"title": "Valid title", "status": "invalid-status"},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="body.status",
        )

    def test_create_task_invalid_priority_enum(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.post(
            "/tasks/",
            headers=admin_headers,
            json={"title": "Valid title", "priority": "urgent"},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="body.priority",
        )

    def test_update_task_title_too_short(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        created = create_task_via_api(client, admin_headers, title="Valid title")

        response = client.put(
            f"/tasks/{created['id']}",
            headers=admin_headers,
            json={"title": "ab"},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains=f"at least {TITLE_MIN_LENGTH} characters",
        )

    def test_update_task_invalid_status_enum(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        created = create_task_via_api(client, admin_headers, title="Valid title")

        response = client.put(
            f"/tasks/{created['id']}",
            headers=admin_headers,
            json={"status": "invalid-status"},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="body.status",
        )

    def test_list_tasks_invalid_skip(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"skip": -1})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail="skip: Input should be greater than or equal to 0",
        )

    def test_list_tasks_invalid_limit(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"limit": 0})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail="limit: Input should be greater than or equal to 1",
        )

    def test_list_tasks_limit_above_max(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"limit": 101})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail="limit: Input should be less than or equal to 100",
        )

    def test_list_tasks_invalid_status_filter(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"status": "invalid"})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="status:",
        )

    def test_list_tasks_invalid_priority_filter(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"priority": "urgent"})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="priority:",
        )

    def test_list_tasks_empty_search(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"search": "   "})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail="search: Value error, search cannot be empty",
        )

    def test_list_tasks_search_too_long(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get(
            "/tasks/",
            headers=admin_headers,
            params={"search": "x" * 121},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail="search: String should have at most 120 characters",
        )

    def test_list_tasks_invalid_sort_by(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"sort_by": "title"})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="sort_by:",
        )

    def test_list_tasks_invalid_sort_order(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/", headers=admin_headers, params={"sort_order": "up"})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="sort_order:",
        )

    def test_login_missing_credentials(self, client: TestClient, seed_admin) -> None:
        response = client.post("/auth/login", json={})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="body.username",
        )

    def test_login_missing_password(self, client: TestClient, seed_admin) -> None:
        response = client.post("/auth/login", json={"username": "testadmin"})

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="body.password",
        )

    def test_login_rejects_empty_username(self, client: TestClient, seed_admin) -> None:
        response = client.post(
            "/auth/login",
            json={"username": "", "password": "any-password"},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="body.username",
        )

    def test_login_rejects_empty_password(self, client: TestClient, seed_admin) -> None:
        response = client.post(
            "/auth/login",
            json={"username": "testadmin", "password": ""},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="body.password",
        )

    def test_login_rejects_username_over_max_length(
        self,
        client: TestClient,
        seed_admin,
    ) -> None:
        response = client.post(
            "/auth/login",
            json={"username": "a" * 51, "password": "any-password"},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="body.username",
        )

    def test_login_rejects_password_over_max_length(
        self,
        client: TestClient,
        seed_admin,
    ) -> None:
        response = client.post(
            "/auth/login",
            json={"username": "testadmin", "password": "a" * 129},
        )

        assert_error(
            response,
            status_code=422,
            code="validation_error",
            detail_contains="body.password",
        )
