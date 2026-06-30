from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limit import LOGIN_RATE_LIMIT, limiter
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.domain.user import UserEntity
from app.api.mappers import auth_result_to_response, user_to_response
from app.api.openapi_responses import (
    RESPONSES_INVALID_CREDENTIALS,
    RESPONSES_RATE_LIMITED,
    RESPONSES_UNAUTHORIZED,
    merge_responses,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate with username and password",
    description=(
        "Validate credentials and return a JWT access token. "
        "Use the token in subsequent requests: `Authorization: Bearer <access_token>`.\n\n"
        "Rate limit: 5 requests per minute per client IP."
    ),
    response_description="JWT access token and user role",
    responses=merge_responses(RESPONSES_INVALID_CREDENTIALS, RESPONSES_RATE_LIMITED),
)
@limiter.limit(LOGIN_RATE_LIMIT)
def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    result = service.authenticate(login_data.username, login_data.password)
    return auth_result_to_response(result)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Return the authenticated user's username and role from the Bearer token.",
    response_description="Current user profile",
    responses=RESPONSES_UNAUTHORIZED,
)
def get_me(
    current_user: UserEntity = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    user = service.get_user_by_username(current_user.username)
    return user_to_response(user)
