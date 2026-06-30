import pytest

from app.core.config import Settings
from app.core.cors import build_cors_middleware_kwargs


def _set_development_env(monkeypatch: pytest.MonkeyPatch, **overrides: str) -> None:
    defaults = {
        "ENVIRONMENT": "development",
        "SECRET_KEY": "test-secret",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "DATABASE_URL": "sqlite://",
        "BOOTSTRAP_ADMIN_USERNAME": "admin",
        "BOOTSTRAP_ADMIN_PASSWORD": "password",
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        monkeypatch.setenv(key, value)


class TestBuildCorsMiddlewareKwargs:
    def test_development_without_explicit_origins_defaults_to_localhost_3000(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_development_env(monkeypatch)
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        settings = Settings()

        kwargs = build_cors_middleware_kwargs(settings)

        assert kwargs["allow_origins"] == ["http://localhost:3000"]
        assert kwargs["allow_credentials"] is True

    def test_development_with_explicit_origins_uses_allow_origins(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_development_env(monkeypatch, CORS_ORIGINS="https://app.example.com")
        settings = Settings()

        kwargs = build_cors_middleware_kwargs(settings)

        assert kwargs["allow_origins"] == ["https://app.example.com"]
        assert kwargs["allow_credentials"] is True

    def test_production_uses_explicit_origins_only(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_development_env(
            monkeypatch,
            ENVIRONMENT="production",
            SECRET_KEY="production-secret-key-with-32-chars-min",
            BOOTSTRAP_ADMIN_PASSWORD="secure-bootstrap-password",
            CORS_ORIGINS="https://app.example.com",
        )
        settings = Settings()

        kwargs = build_cors_middleware_kwargs(settings)

        assert kwargs["allow_origins"] == ["https://app.example.com"]
        assert kwargs["allow_credentials"] is True
        assert "*" not in kwargs["allow_methods"]
        assert "*" not in kwargs["allow_headers"]
