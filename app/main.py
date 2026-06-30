import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.task_router import router as task_router
from app.api.auth_router import router as auth_router
from app.core.bootstrap import ensure_default_admin
from app.core.config import settings
from app.core.cors import build_cors_middleware_kwargs
from app.core.database import SessionLocal, get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.health import health_check_response
from app.core.rate_limit import configure_rate_limiting
from app.schemas.common import ApiInfoResponse, HealthResponse

logger = logging.getLogger(__name__)

OPENAPI_TAGS = [
    {
        "name": "auth",
        "description": "Authentication and current-user profile",
    },
    {
        "name": "tasks",
        "description": "Task CRUD with filtering, search, and role-based delete",
    },
    {
        "name": "system",
        "description": "Service metadata and health checks",
    },
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = SessionLocal()
    try:
        if settings.is_production:
            logger.info(
                "Production mode: automatic admin bootstrap is disabled. "
                "Create an admin with scripts/seed_admin.py"
            )
        elif ensure_default_admin(db):
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
    finally:
        db.close()
    yield


app = FastAPI(
    title="Task Flow API",
    version="1.0.0",
    lifespan=lifespan,
    description=(
        "REST API for task management with JWT authentication.\n\n"
        "**Authentication:** obtain a token via `POST /auth/login`, "
        "then send `Authorization: Bearer <access_token>` on protected routes.\n\n"
        "**Login rate limit:** 5 requests per minute per client IP "
        "(HTTP 429 when exceeded).\n\n"
        '**Errors:** failures return JSON `{"detail": "...", "code": "..."}`.'
    ),
    openapi_tags=OPENAPI_TAGS,
)

app.add_middleware(
    CORSMiddleware,
    **build_cors_middleware_kwargs(settings),
)

register_exception_handlers(app)
configure_rate_limiting(app)

app.include_router(auth_router)
app.include_router(task_router)


@app.get(
    "/",
    response_model=ApiInfoResponse,
    tags=["system"],
    summary="API metadata",
    description="Return API name and version.",
    response_description="API name and version",
)
def root():
    return {"message": "Task Flow API", "version": "1.0.0"}


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
    description=(
        "Readiness probe for load balancers and orchestrators. "
        "Verifies database connectivity with `SELECT 1`."
    ),
    response_description="Service health status",
    responses={
        503: {
            "description": "Database is unavailable",
            "content": {
                "application/json": {
                    "example": {"status": "degraded"},
                }
            },
        }
    },
)
def health_check(db: Session = Depends(get_db)):
    return health_check_response(db)
