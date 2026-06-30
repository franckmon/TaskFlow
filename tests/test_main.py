from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from tests.http_client import TestClient


@pytest.fixture
def main_client(engine) -> Generator[TestClient, None, None]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


class TestMainApplication:
    def test_root_endpoint(self, main_client: TestClient) -> None:
        response = main_client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Task Flow API", "version": "1.0.0"}

    def test_health_endpoint(self, main_client: TestClient) -> None:
        response = main_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_endpoint_returns_503_when_database_is_unavailable(
        self,
        main_client: TestClient,
    ) -> None:
        with patch("app.core.health.check_database_health", return_value=False):
            response = main_client.get("/health")

        assert response.status_code == 503
        assert response.json() == {"status": "degraded"}

    def test_cors_allows_localhost_origin_on_preflight(self, main_client: TestClient) -> None:
        response = main_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_includes_allow_credentials_for_localhost(self, main_client: TestClient) -> None:
        response = main_client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_cors_omits_unlisted_origin(self, main_client: TestClient) -> None:
        response = main_client.get(
            "/health",
            headers={"Origin": "http://evil.example"},
        )

        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") is None

    @patch("app.main.ensure_default_admin", return_value=True)
    def test_lifespan_commits_when_admin_is_created(
        self,
        mock_ensure_default_admin: MagicMock,
        engine,
    ) -> None:
        mock_db = MagicMock()

        with patch("app.main.SessionLocal", return_value=mock_db):
            from app.main import app

            with TestClient(app):
                pass

        mock_ensure_default_admin.assert_called_once_with(mock_db)
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("app.main.ensure_default_admin", return_value=True)
    def test_lifespan_rolls_back_when_commit_raises_integrity_error(
        self,
        mock_ensure_default_admin: MagicMock,
        engine,
    ) -> None:
        mock_db = MagicMock()
        mock_db.commit.side_effect = IntegrityError(
            "INSERT",
            {},
            Exception("UNIQUE constraint failed"),
        )

        with patch("app.main.SessionLocal", return_value=mock_db):
            from app.main import app

            with TestClient(app):
                pass

        mock_ensure_default_admin.assert_called_once_with(mock_db)
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("app.main.ensure_default_admin")
    def test_lifespan_skips_bootstrap_in_production(
        self,
        mock_ensure_default_admin: MagicMock,
        engine,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "production-secret-key-with-32-chars-min")
        monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "secure-bootstrap-password")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")

        from app.core.config import Settings

        production_settings = Settings()

        mock_db = MagicMock()

        with patch("app.main.SessionLocal", return_value=mock_db):
            with patch("app.main.settings", production_settings):
                from app.main import app

                with TestClient(app):
                    pass

        mock_ensure_default_admin.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.close.assert_called_once()
