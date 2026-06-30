import ipaddress
import json
import logging
import os
from typing import Any, Literal, Self, Tuple

from pydantic import Field, field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from app.core.client_ip import parse_trusted_proxies
from app.core.cors_constants import PRODUCTION_CORS_HEADERS, PRODUCTION_CORS_METHODS

logger = logging.getLogger(__name__)

WEAK_SECRET_KEYS = frozenset(
    {
        "your-secret-key-change-in-production",
        "changeme",
        "secret",
        "password",
        "admin",
        "test-secret",
        "test-secret-key",
        "test-secret-key-for-pytest-only",
    }
)

WEAK_BOOTSTRAP_PASSWORDS = frozenset(
    {
        "admin",
        "password",
        "changeme",
        "123456",
    }
)


class _EnvSettingsSource(EnvSettingsSource):
    """Pass CORS_ORIGINS through without JSON decoding."""

    def prepare_field_value(
        self,
        field_name: str,
        field: Any,
        field_value: Any,
        value_is_complex: bool,
    ) -> Any:
        if field_name == "CORS_ORIGINS":
            return field_value
        return super().prepare_field_value(field_name, field, field_value, value_is_complex)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=None,
        secrets_dir=None,
    )

    ENVIRONMENT: Literal["development", "production"]
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(ge=1)
    DATABASE_URL: str
    BOOTSTRAP_ADMIN_USERNAME: str
    BOOTSTRAP_ADMIN_PASSWORD: str
    CORS_ORIGINS: list[str] = Field(default_factory=list)
    TRUSTED_PROXIES: str = Field(default="")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            if not value.strip():
                return []
            stripped = value.strip()
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ORIGINS JSON value must be an array")
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        raise ValueError("CORS_ORIGINS must be a comma-separated list or JSON array")

    @field_validator("TRUSTED_PROXIES", mode="before")
    @classmethod
    def validate_trusted_proxies(cls, value: object) -> str:
        normalized = "" if value is None else str(value)
        parse_trusted_proxies(normalized)
        return normalized

    @property
    def trusted_proxies(self) -> tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]:
        return parse_trusted_proxies(self.TRUSTED_PROXIES)

    @property
    def cors_origins(self) -> list[str]:
        if self.CORS_ORIGINS:
            return self.CORS_ORIGINS
        if not self.is_production:
            return ["http://localhost:3000"]
        return []

    @property
    def cors_allow_credentials(self) -> bool:
        if self.CORS_ORIGINS:
            return "*" not in self.CORS_ORIGINS
        return not self.is_production

    @property
    def cors_allow_methods(self) -> list[str]:
        if self.is_production:
            return list(PRODUCTION_CORS_METHODS)
        return ["*"]

    @property
    def cors_allow_headers(self) -> list[str]:
        if self.is_production:
            return list(PRODUCTION_CORS_HEADERS)
        return ["*"]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @model_validator(mode="after")
    def validate_environment_config(self) -> Self:
        if self.is_production:
            self._validate_production_config()
        else:
            self._warn_insecure_development_defaults()
        return self

    def _validate_production_config(self) -> None:
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")

        if self.SECRET_KEY.lower() in WEAK_SECRET_KEYS:
            raise ValueError("SECRET_KEY is too weak for production")

        if self.BOOTSTRAP_ADMIN_PASSWORD.lower() in WEAK_BOOTSTRAP_PASSWORDS:
            raise ValueError("BOOTSTRAP_ADMIN_PASSWORD is too weak for production")

        if "CORS_ORIGINS" not in os.environ:
            raise ValueError("CORS_ORIGINS must be set in production")

        if not self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must not be empty in production")

        if "*" in self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must not contain wildcard in production")

    def _warn_insecure_development_defaults(self) -> None:
        if len(self.SECRET_KEY) < 32:
            logger.warning(
                "SECRET_KEY is shorter than 32 characters; use a stronger key before production"
            )

        if self.SECRET_KEY.lower() in WEAK_SECRET_KEYS:
            logger.warning(
                "SECRET_KEY matches a known insecure default; change it before production"
            )

        if self.BOOTSTRAP_ADMIN_PASSWORD.lower() in WEAK_BOOTSTRAP_PASSWORDS:
            logger.warning(
                "BOOTSTRAP_ADMIN_PASSWORD matches a known insecure default; "
                "change it before production"
            )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # Environment variables only — pydantic does not load .env or constructor kwargs.
        return (_EnvSettingsSource(settings_cls),)


settings = Settings()
