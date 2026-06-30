from fastapi.testclient import TestClient

from tests.api.conftest import create_task_via_api


class TestTaskCreate:
    def test_create_task(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        response = client.post(
            "/tasks/",
            headers=admin_headers,
            json={
                "title": "Deploy release",
                "description": "Release notes",
                "status": "new",
                "priority": "high",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] > 0
        assert payload["title"] == "Deploy release"
        assert payload["description"] == "Release notes"
        assert payload["status"] == "new"
        assert payload["priority"] == "high"
        assert "created_at" in payload
        assert "updated_at" in payload

    def test_create_requires_authentication(self, client: TestClient) -> None:
        response = client.post(
            "/tasks/",
            json={"title": "Unauthorized task"},
        )

        assert response.status_code == 403

    def test_create_rejects_invalid_initial_status(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.post(
            "/tasks/",
            headers=admin_headers,
            json={
                "title": "Invalid status task",
                "status": "in_progress",
            },
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "New tasks must start with status 'new'",
            "code": "invalid_status_transition",
        }


class TestTaskRead:
    def test_get_task_by_id(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        created = create_task_via_api(client, admin_headers, title="Single task")

        response = client.get(f"/tasks/{created['id']}", headers=admin_headers)

        assert response.status_code == 200
        assert response.json() == created

    def test_get_missing_task_returns_404(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/tasks/99999", headers=admin_headers)

        assert response.status_code == 404
        assert response.json() == {"detail": "Task not found", "code": "task_not_found"}


class TestTaskList:
    def test_list_tasks(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        first = create_task_via_api(client, admin_headers, title="First task")
        second = create_task_via_api(client, admin_headers, title="Second task")

        response = client.get("/tasks/", headers=admin_headers)

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) >= 2
        titles = {task["title"] for task in payload}
        assert {first["title"], second["title"]}.issubset(titles)

    def test_search_tasks(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        create_task_via_api(client, admin_headers, title="Billing report", description="finance")
        create_task_via_api(client, admin_headers, title="Unrelated", description="other")

        response = client.get("/tasks/", headers=admin_headers, params={"search": "billing"})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["title"] == "Billing report"

    def test_filter_by_status(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        create_task_via_api(client, admin_headers, title="Open task", status="new")
        done = create_task_via_api(client, admin_headers, title="Finished task", status="new")
        client.put(
            f"/tasks/{done['id']}",
            headers=admin_headers,
            json={"status": "in_progress"},
        )
        client.put(
            f"/tasks/{done['id']}",
            headers=admin_headers,
            json={"status": "done"},
        )

        response = client.get("/tasks/", headers=admin_headers, params={"status": "done"})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["title"] == "Finished task"
        assert payload[0]["status"] == "done"

    def test_filter_by_priority(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        create_task_via_api(client, admin_headers, title="Low task", priority="low")
        create_task_via_api(client, admin_headers, title="High task", priority="high")

        response = client.get("/tasks/", headers=admin_headers, params={"priority": "high"})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["title"] == "High task"

    def test_sort_tasks(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        create_task_via_api(client, admin_headers, title="Alpha task")
        create_task_via_api(client, admin_headers, title="Beta task")

        response = client.get(
            "/tasks/",
            headers=admin_headers,
            params={"sort_by": "created_at", "sort_order": "asc"},
        )

        assert response.status_code == 200
        titles = [
            task["title"]
            for task in response.json()
            if task["title"] in {"Alpha task", "Beta task"}
        ]
        assert titles == ["Alpha task", "Beta task"]

    def test_paginate_tasks(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        for index in range(3):
            create_task_via_api(client, admin_headers, title=f"Paged task {index}")

        response = client.get(
            "/tasks/",
            headers=admin_headers,
            params={"skip": 1, "limit": 1, "sort_by": "created_at", "sort_order": "asc"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["title"] == "Paged task 1"


class TestTaskUpdate:
    def test_update_task(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        created = create_task_via_api(client, admin_headers, title="Original title")

        response = client.put(
            f"/tasks/{created['id']}",
            headers=admin_headers,
            json={
                "title": "Updated title",
                "description": "Updated description",
                "status": "in_progress",
                "priority": "high",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["title"] == "Updated title"
        assert payload["description"] == "Updated description"
        assert payload["status"] == "in_progress"
        assert payload["priority"] == "high"

    def test_update_completed_task_is_forbidden(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        created = create_task_via_api(client, admin_headers, title="Completed task")
        client.put(f"/tasks/{created['id']}", headers=admin_headers, json={"status": "in_progress"})
        client.put(f"/tasks/{created['id']}", headers=admin_headers, json={"status": "done"})

        response = client.put(
            f"/tasks/{created['id']}",
            headers=admin_headers,
            json={"title": "Should fail"},
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "Cannot edit a completed task",
            "code": "task_completed",
        }

    def test_update_with_invalid_transition(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        created = create_task_via_api(client, admin_headers, title="Transition task")

        response = client.put(
            f"/tasks/{created['id']}",
            headers=admin_headers,
            json={"status": "done"},
        )

        assert response.status_code == 400
        assert response.json() == {
            "detail": "Invalid status transition from 'new' to 'done'",
            "code": "invalid_status_transition",
        }


class TestTaskDelete:
    def test_admin_can_delete_task(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        created = create_task_via_api(client, admin_headers, title="Delete me")

        response = client.delete(f"/tasks/{created['id']}", headers=admin_headers)

        assert response.status_code == 200
        assert response.json() == {"message": "Task deleted successfully"}

        get_response = client.get(f"/tasks/{created['id']}", headers=admin_headers)
        assert get_response.status_code == 404

    def test_non_admin_cannot_delete_task(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        user_headers: dict[str, str],
    ) -> None:
        created = create_task_via_api(client, admin_headers, title="Protected task")

        response = client.delete(f"/tasks/{created['id']}", headers=user_headers)

        assert response.status_code == 403
        assert response.json() == {
            "detail": "Only admin users can delete tasks",
            "code": "permission_denied",
        }

        still_exists = client.get(f"/tasks/{created['id']}", headers=admin_headers)
        assert still_exists.status_code == 200

    def test_admin_can_delete_completed_task(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        created = create_task_via_api(client, admin_headers, title="Completed delete")
        client.put(f"/tasks/{created['id']}", headers=admin_headers, json={"status": "in_progress"})
        client.put(f"/tasks/{created['id']}", headers=admin_headers, json={"status": "done"})

        response = client.delete(f"/tasks/{created['id']}", headers=admin_headers)

        assert response.status_code == 200
        assert response.json() == {"message": "Task deleted successfully"}
