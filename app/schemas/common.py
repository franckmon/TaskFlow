from pydantic import BaseModel, ConfigDict, Field


class MessageResponse(BaseModel):
    """Confirmation message returned after a successful action."""

    message: str = Field(..., description="Human-readable result message")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"message": "Task deleted successfully"}],
        }
    )


class ErrorResponse(BaseModel):
    """Standard JSON error body for application and validation failures."""

    detail: str = Field(..., description="Human-readable error message")
    code: str = Field(
        ...,
        description="Machine-readable error code (for example `task_not_found`, `invalid_credentials`)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Task not found", "code": "task_not_found"},
            ]
        }
    )


class ApiInfoResponse(BaseModel):
    """API metadata returned by the root endpoint."""

    message: str = Field(..., description="API name")
    version: str = Field(..., description="Semantic API version")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"message": "Task Flow API", "version": "1.0.0"}],
        }
    )


class HealthResponse(BaseModel):
    """Health probe response."""

    status: str = Field(..., description="Service health indicator")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"status": "ok"}],
        }
    )
