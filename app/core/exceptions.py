class AppError(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BusinessLogicError(AppError):
    status_code = 400
    code = "business_logic_error"


class TaskCompletedError(BusinessLogicError):
    code = "task_completed"


class InvalidStatusTransitionError(BusinessLogicError):
    code = "invalid_status_transition"


class PermissionDeniedError(AppError):
    status_code = 403
    code = "permission_denied"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class TaskNotFoundError(NotFoundError):
    code = "task_not_found"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class InvalidCredentialsError(UnauthorizedError):
    code = "invalid_credentials"
