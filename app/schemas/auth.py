from pydantic import BaseModel, ConfigDict, Field

from app.domain.user_types import UserRole

USERNAME_MIN_LENGTH = 1
USERNAME_MAX_LENGTH = 50
PASSWORD_MIN_LENGTH = 1
PASSWORD_MAX_LENGTH = 128


class LoginRequest(BaseModel):
    """Credentials for `POST /auth/login`."""

    username: str = Field(
        ...,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        description=(f"Account username ({USERNAME_MIN_LENGTH}–{USERNAME_MAX_LENGTH} characters)"),
        examples=["admin"],
    )
    password: str = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description=(
            f"Plain-text password ({PASSWORD_MIN_LENGTH}–{PASSWORD_MAX_LENGTH} characters)"
        ),
        examples=["admin"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"username": "admin", "password": "admin"},
            ]
        }
    )


class TokenResponse(BaseModel):
    """JWT issued after successful authentication."""

    access_token: str = Field(
        ...,
        description="Signed JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        description="Token type for the Authorization header",
        examples=["bearer"],
    )
    role: UserRole = Field(..., description="Role of the authenticated user")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "role": "admin",
                }
            ]
        }
    )


class UserResponse(BaseModel):
    """Public user profile."""

    username: str = Field(..., description="Unique username", examples=["admin"])
    role: UserRole = Field(..., description="User role (`admin` or `user`)")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {"username": "admin", "role": "admin"},
            ]
        },
    )
