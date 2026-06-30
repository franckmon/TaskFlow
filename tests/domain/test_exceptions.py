import pytest

from app.core.exceptions import (
    AppError,
    BusinessLogicError,
    InvalidCredentialsError,
    InvalidStatusTransitionError,
    NotFoundError,
    PermissionDeniedError,
    TaskCompletedError,
    TaskNotFoundError,
    UnauthorizedError,
)


@pytest.mark.parametrize(
    ("exc_type", "status_code", "code"),
    [
        (BusinessLogicError, 400, "business_logic_error"),
        (TaskCompletedError, 400, "task_completed"),
        (InvalidStatusTransitionError, 400, "invalid_status_transition"),
        (PermissionDeniedError, 403, "permission_denied"),
        (NotFoundError, 404, "not_found"),
        (TaskNotFoundError, 404, "task_not_found"),
        (UnauthorizedError, 401, "unauthorized"),
        (InvalidCredentialsError, 401, "invalid_credentials"),
    ],
)
def test_exception_metadata(exc_type: type[AppError], status_code: int, code: str) -> None:
    error = exc_type("test message")

    assert isinstance(error, AppError)
    assert error.message == "test message"
    assert error.status_code == status_code
    assert error.code == code
    assert str(error) == "test message"


def test_default_app_error_metadata() -> None:
    error = AppError("internal failure")

    assert error.status_code == 500
    assert error.code == "internal_error"
