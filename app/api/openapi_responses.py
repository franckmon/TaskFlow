from typing import Any

from app.schemas.common import ErrorResponse

_ERROR_CONTENT = "application/json"


def _error(
    description: str,
    detail: str,
    code: str,
) -> dict[str, Any]:
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {
            _ERROR_CONTENT: {
                "example": {"detail": detail, "code": code},
            }
        },
    }


RESPONSES_UNAUTHORIZED: dict[int, dict[str, Any]] = {
    401: _error(
        "Missing, expired, or invalid Bearer token",
        "Invalid authentication credentials",
        "unauthorized",
    ),
}

RESPONSES_INVALID_CREDENTIALS: dict[int, dict[str, Any]] = {
    401: _error(
        "Username or password is incorrect",
        "Incorrect username or password",
        "invalid_credentials",
    ),
}

RESPONSES_RATE_LIMITED: dict[int, dict[str, Any]] = {
    429: _error(
        "Too many login attempts from this IP address",
        "Too many login attempts. Please try again later.",
        "rate_limit_exceeded",
    ),
}

RESPONSES_FORBIDDEN: dict[int, dict[str, Any]] = {
    403: _error(
        "Authenticated user lacks permission for this action",
        "Only admin users can delete tasks",
        "permission_denied",
    ),
}

RESPONSES_NOT_FOUND: dict[int, dict[str, Any]] = {
    404: _error(
        "Requested task does not exist",
        "Task not found",
        "task_not_found",
    ),
}

RESPONSES_VALIDATION: dict[int, dict[str, Any]] = {
    422: _error(
        "Request body or query parameters failed validation",
        "search cannot be empty",
        "validation_error",
    ),
}

RESPONSES_TASK_COMPLETED: dict[int, dict[str, Any]] = {
    400: _error(
        "Operation conflicts with a completed (done) task",
        "Cannot edit a completed task",
        "task_completed",
    ),
}

RESPONSES_INVALID_STATUS: dict[int, dict[str, Any]] = {
    400: _error(
        "Task status change violates the allowed workflow (new → in_progress → done)",
        "Invalid status transition from 'new' to 'done'",
        "invalid_status_transition",
    ),
}


def merge_responses(*groups: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    merged: dict[int, dict[str, Any]] = {}
    for group in groups:
        merged.update(group)
    return merged
