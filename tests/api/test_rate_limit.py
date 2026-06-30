from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

import app.core.config as config_module
from app.core.rate_limit import limiter, reset_rate_limits


@pytest.fixture
def rate_limited_client(client: TestClient) -> Generator[TestClient, None, None]:
    limiter.enabled = True
    reset_rate_limits()
    try:
        yield client
    finally:
        limiter.enabled = False
        reset_rate_limits()


def _reload_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    config_module.settings = config_module.Settings()


class TestLoginRateLimit:
    def test_login_allows_up_to_five_requests_per_minute(
        self,
        rate_limited_client: TestClient,
        seed_admin,
        admin_credentials: dict[str, str],
    ) -> None:
        for _ in range(5):
            response = rate_limited_client.post("/auth/login", json=admin_credentials)
            assert response.status_code == 200

    def test_login_returns_429_after_limit_is_exceeded(
        self,
        rate_limited_client: TestClient,
        seed_admin,
        admin_credentials: dict[str, str],
    ) -> None:
        for _ in range(5):
            rate_limited_client.post("/auth/login", json=admin_credentials)

        response = rate_limited_client.post("/auth/login", json=admin_credentials)

        assert response.status_code == 429
        assert response.json() == {
            "detail": "Too many login attempts. Please try again later.",
            "code": "rate_limit_exceeded",
        }

    def test_failed_login_attempts_count_toward_rate_limit(
        self,
        rate_limited_client: TestClient,
        seed_admin,
    ) -> None:
        invalid_credentials = {"username": "testadmin", "password": "wrong-password"}

        for _ in range(5):
            response = rate_limited_client.post("/auth/login", json=invalid_credentials)
            assert response.status_code == 401

        response = rate_limited_client.post("/auth/login", json=invalid_credentials)

        assert response.status_code == 429
        assert response.json()["code"] == "rate_limit_exceeded"

    def test_me_endpoint_is_not_rate_limited(
        self,
        rate_limited_client: TestClient,
        admin_headers: dict[str, str],
    ) -> None:
        for _ in range(6):
            response = rate_limited_client.get("/auth/me", headers=admin_headers)
            assert response.status_code == 200


class TestLoginRateLimitClientIp:
    def test_rate_limit_uses_forwarded_ip_behind_trusted_proxy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        rate_limited_client: TestClient,
        seed_admin,
        admin_credentials: dict[str, str],
    ) -> None:
        monkeypatch.setenv("TRUSTED_PROXIES", "127.0.0.1")
        _reload_settings(monkeypatch)
        reset_rate_limits()

        headers = {"X-Forwarded-For": "203.0.113.10"}

        for _ in range(5):
            response = rate_limited_client.post(
                "/auth/login",
                json=admin_credentials,
                headers=headers,
            )
            assert response.status_code == 200

        response = rate_limited_client.post(
            "/auth/login",
            json=admin_credentials,
            headers=headers,
        )
        assert response.status_code == 429

        reset_rate_limits()
        response = rate_limited_client.post(
            "/auth/login",
            json=admin_credentials,
            headers={"X-Forwarded-For": "198.51.100.20"},
        )
        assert response.status_code == 200

    def test_rate_limit_ignores_spoofed_forwarded_ip_without_trusted_proxy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        rate_limited_client: TestClient,
        seed_admin,
        admin_credentials: dict[str, str],
    ) -> None:
        monkeypatch.delenv("TRUSTED_PROXIES", raising=False)
        _reload_settings(monkeypatch)
        reset_rate_limits()

        headers = {"X-Forwarded-For": "203.0.113.10"}

        for _ in range(5):
            response = rate_limited_client.post(
                "/auth/login",
                json=admin_credentials,
                headers=headers,
            )
            assert response.status_code == 200

        response = rate_limited_client.post(
            "/auth/login",
            json=admin_credentials,
            headers={"X-Forwarded-For": "198.51.100.20"},
        )
        assert response.status_code == 429
