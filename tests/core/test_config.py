import pytest
from pydantic import ValidationError

from app.core.config import WEAK_BOOTSTRAP_PASSWORDS, WEAK_SECRET_KEYS, Settings


def _set_env(monkeypatch: pytest.MonkeyPatch, **values: str | int) -> None:
    for key, value in values.items():
        monkeypatch.setenv(key, str(value))


def _set_valid_production_env(monkeypatch: pytest.MonkeyPatch, **overrides: str | int) -> None:
    defaults = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "production-secret-key-with-32-chars-min",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "DATABASE_URL": "sqlite:///./app.db",
        "BOOTSTRAP_ADMIN_USERNAME": "admin",
        "BOOTSTRAP_ADMIN_PASSWORD": "secure-bootstrap-password",
        "CORS_ORIGINS": "https://app.example.com",
    }
    defaults.update(overrides)
    _set_env(monkeypatch, **defaults)


def _set_development_env(monkeypatch: pytest.MonkeyPatch, **overrides: str | int) -> None:
    defaults = {
        "ENVIRONMENT": "development",
        "SECRET_KEY": "test-secret",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "DATABASE_URL": "sqlite://",
        "BOOTSTRAP_ADMIN_USERNAME": "admin",
        "BOOTSTRAP_ADMIN_PASSWORD": "password",
    }
    defaults.update(overrides)
    _set_env(monkeypatch, **defaults)


class TestSettings:
    def test_is_production_when_environment_is_production(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_valid_production_env(monkeypatch)
        settings = Settings()

        assert settings.is_production is True

    def test_is_production_when_environment_is_development(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_development_env(monkeypatch)
        settings = Settings()

        assert settings.is_production is False


class TestDevelopmentSettings:
    def test_allows_weak_secret_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_development_env(monkeypatch, SECRET_KEY="test-secret")

        settings = Settings()

        assert settings.SECRET_KEY == "test-secret"

    def test_allows_weak_bootstrap_password(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_development_env(monkeypatch, BOOTSTRAP_ADMIN_PASSWORD="password")

        settings = Settings()

        assert settings.BOOTSTRAP_ADMIN_PASSWORD == "password"

    def test_warns_on_insecure_defaults_in_development(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        import logging

        caplog.set_level(logging.WARNING, logger="app.core.config")

        _set_development_env(
            monkeypatch,
            SECRET_KEY="test-secret",
            BOOTSTRAP_ADMIN_PASSWORD="password",
        )

        Settings()

        messages = [record.message for record in caplog.records]
        assert any("SECRET_KEY is shorter than 32 characters" in message for message in messages)
        assert any("SECRET_KEY matches a known insecure default" in message for message in messages)
        assert any(
            "BOOTSTRAP_ADMIN_PASSWORD matches a known insecure default" in message
            for message in messages
        )


class TestCorsSettings:
    def test_uses_localhost_3000_default_in_development(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_development_env(monkeypatch)
        monkeypatch.delenv("CORS_ORIGINS", raising=False)

        settings = Settings()

        assert settings.CORS_ORIGINS == []
        assert settings.cors_origins == ["http://localhost:3000"]
        assert settings.cors_allow_credentials is True

        from app.core.cors import build_cors_middleware_kwargs

        cors_kwargs = build_cors_middleware_kwargs(settings)
        assert cors_kwargs["allow_origins"] == ["http://localhost:3000"]

    def test_parses_comma_separated_origins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_development_env(
            monkeypatch,
            CORS_ORIGINS="https://a.example.com, https://b.example.com",
        )

        settings = Settings()

        assert settings.CORS_ORIGINS == [
            "https://a.example.com",
            "https://b.example.com",
        ]
        assert settings.cors_allow_credentials is True

    def test_requires_cors_origins_in_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_valid_production_env(monkeypatch)
        monkeypatch.delenv("CORS_ORIGINS", raising=False)

        with pytest.raises(ValidationError, match="CORS_ORIGINS must be set in production"):
            Settings()

    def test_rejects_empty_cors_origins_in_production(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_valid_production_env(monkeypatch, CORS_ORIGINS="")

        with pytest.raises(ValidationError, match="CORS_ORIGINS must not be empty in production"):
            Settings()

    def test_rejects_wildcard_cors_origins_in_production(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_valid_production_env(monkeypatch, CORS_ORIGINS="*")

        with pytest.raises(
            ValidationError,
            match="CORS_ORIGINS must not contain wildcard in production",
        ):
            Settings()

    def test_disables_credentials_for_wildcard_origins_in_development(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_development_env(monkeypatch, CORS_ORIGINS="*")

        settings = Settings()

        assert settings.cors_allow_credentials is False

    def test_production_uses_explicit_methods_and_headers(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_valid_production_env(monkeypatch)

        settings = Settings()

        assert "*" not in settings.cors_allow_methods
        assert "*" not in settings.cors_allow_headers


class TestProductionSettingsValidation:
    def test_accepts_strong_production_configuration(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_valid_production_env(monkeypatch)

        settings = Settings()

        assert settings.is_production is True
        assert len(settings.SECRET_KEY) >= 32

    def test_rejects_short_secret_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_valid_production_env(monkeypatch, SECRET_KEY="too-short")

        with pytest.raises(ValidationError, match="SECRET_KEY must be at least 32 characters"):
            Settings()

    @pytest.mark.parametrize(
        "weak_key",
        [key for key in sorted(WEAK_SECRET_KEYS) if len(key) >= 32],
    )
    def test_rejects_obvious_weak_secret_keys(
        self,
        monkeypatch: pytest.MonkeyPatch,
        weak_key: str,
    ) -> None:
        _set_valid_production_env(monkeypatch, SECRET_KEY=weak_key)

        with pytest.raises(ValidationError, match="SECRET_KEY is too weak for production"):
            Settings()

    @pytest.mark.parametrize("weak_password", sorted(WEAK_BOOTSTRAP_PASSWORDS))
    def test_rejects_weak_bootstrap_passwords(
        self,
        monkeypatch: pytest.MonkeyPatch,
        weak_password: str,
    ) -> None:
        _set_valid_production_env(monkeypatch, BOOTSTRAP_ADMIN_PASSWORD=weak_password)

        with pytest.raises(
            ValidationError,
            match="BOOTSTRAP_ADMIN_PASSWORD is too weak for production",
        ):
            Settings()

    def test_rejects_weak_bootstrap_password_case_insensitively(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_valid_production_env(monkeypatch, BOOTSTRAP_ADMIN_PASSWORD="ADMIN")

        with pytest.raises(
            ValidationError,
            match="BOOTSTRAP_ADMIN_PASSWORD is too weak for production",
        ):
            Settings()

    def test_raises_validation_error_at_startup(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_valid_production_env(monkeypatch, BOOTSTRAP_ADMIN_PASSWORD="admin")

        with pytest.raises(ValidationError):
            Settings()


class TestTrustedProxiesSettings:
    def test_allows_empty_trusted_proxies(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_development_env(monkeypatch, TRUSTED_PROXIES="")

        settings = Settings()

        assert settings.trusted_proxies == ()

    def test_rejects_invalid_trusted_proxy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_development_env(monkeypatch, TRUSTED_PROXIES="not-an-ip")

        with pytest.raises(ValidationError):
            Settings()
