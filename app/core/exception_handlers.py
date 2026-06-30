from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.exceptions import AppError


def _error_content(detail: str, code: str) -> dict[str, str]:
    return {"detail": detail, "code": code}


def _format_validation_errors(errors: list[dict]) -> str:
    messages = [
        f"{'.'.join(str(part) for part in error.get('loc', []))}: {error.get('msg', 'Invalid value')}"
        for error in errors
    ]
    return "; ".join(messages) if messages else "Validation error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_content(exc.message, exc.code),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        code = {
            400: "bad_request",
            401: "unauthorized",
            403: "permission_denied",
            404: "not_found",
            422: "validation_error",
            429: "rate_limit_exceeded",
        }.get(exc.status_code, "http_error")

        return JSONResponse(
            status_code=exc.status_code,
            content=_error_content(detail, code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_content(_format_validation_errors(exc.errors()), "validation_error"),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        _request: Request, exc: ValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_content(_format_validation_errors(exc.errors()), "validation_error"),
        )
