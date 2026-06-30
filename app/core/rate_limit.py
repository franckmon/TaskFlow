from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.client_ip import get_client_ip

LOGIN_RATE_LIMIT = "5/minute"

limiter = Limiter(
    key_func=get_client_ip,
    storage_uri="memory://",
)


async def rate_limit_exceeded_handler(
    _request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many login attempts. Please try again later.",
            "code": "rate_limit_exceeded",
        },
        headers=exc.headers,
    )


def configure_rate_limiting(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)


def reset_rate_limits() -> None:
    """Clear in-memory counters. Intended for tests."""
    limiter._storage.reset()
