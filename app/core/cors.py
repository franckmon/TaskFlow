from typing import Any

from app.core.config import Settings


def build_cors_middleware_kwargs(settings: Settings) -> dict[str, Any]:
    return {
        "allow_origins": settings.cors_origins,
        "allow_credentials": settings.cors_allow_credentials,
        "allow_methods": settings.cors_allow_methods,
        "allow_headers": settings.cors_allow_headers,
    }
