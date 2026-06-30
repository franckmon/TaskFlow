from fastapi.testclient import TestClient


class TestLogin:
    def test_login_success(
        self,
        client: TestClient,
        seed_admin,
        admin_credentials: dict[str, str],
    ) -> None:
        response = client.post("/auth/login", json=admin_credentials)

        assert response.status_code == 200
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["role"] == "admin"
        assert isinstance(payload["access_token"], str)
        assert payload["access_token"]

    def test_login_failure(self, client: TestClient, seed_admin) -> None:
        response = client.post(
            "/auth/login",
            json={"username": "testadmin", "password": "wrong-password"},
        )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Incorrect username or password",
            "code": "invalid_credentials",
        }

    def test_login_accepts_credentials_at_max_length(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        from app.core.security import get_password_hash
        from app.domain.user_types import UserRole
        from app.models.user import User

        username = "a" * 50
        password = "b" * 128
        db_session.add(
            User(
                username=username,
                hashed_password=get_password_hash(password),
                role=UserRole.USER,
            )
        )
        db_session.flush()

        response = client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )

        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"


class TestMe:
    def test_get_current_user(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        response = client.get("/auth/me", headers=admin_headers)

        assert response.status_code == 200
        assert response.json() == {"username": "testadmin", "role": "admin"}

    def test_get_current_user_requires_auth(self, client: TestClient) -> None:
        response = client.get("/auth/me")

        assert response.status_code == 403
