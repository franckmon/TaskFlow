import os
import warnings
from collections.abc import Generator

warnings.filterwarnings(
    "ignore",
    message=r"'crypt' is deprecated and slated for removal",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"datetime\.datetime\.utcnow\(\) is deprecated",
    category=DeprecationWarning,
)

from fastapi import Depends, FastAPI
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

TEST_DB_URL = "sqlite://"
_DEV_DATABASE_MARKERS = ("./app.db", "app.db")

os.environ.update(
    {
        "ENVIRONMENT": "development",
        "DATABASE_URL": TEST_DB_URL,
        "SECRET_KEY": "test-secret-key-for-pytest-only",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "BOOTSTRAP_ADMIN_USERNAME": "testadmin",
        "BOOTSTRAP_ADMIN_PASSWORD": "testpassword",
        "RATELIMIT_ENABLED": "false",
    }
)

if any(marker in os.environ.get("DATABASE_URL", "") for marker in _DEV_DATABASE_MARKERS):
    raise RuntimeError("Tests must not use the development database")

import pytest

pytest_plugins = ["tests.api.conftest"]

from app.api.auth_router import router as auth_router
from app.api.task_router import router as task_router
from app.core.database import Base, get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.health import health_check_response
from app.core.rate_limit import configure_rate_limiting
import app.models.task  # noqa: F401
import app.models.user  # noqa: F401
from tests.http_client import TestClient


def create_test_app() -> FastAPI:
    test_app = FastAPI(title="Task Flow API", version="1.0.0")
    register_exception_handlers(test_app)
    configure_rate_limiting(test_app)
    test_app.include_router(auth_router)
    test_app.include_router(task_router)

    @test_app.get("/")
    def root():
        return {"message": "Task Flow API", "version": "1.0.0"}

    @test_app.get("/health")
    def health_check(db: Session = Depends(get_db)):
        return health_check_response(db)

    return test_app


@pytest.fixture(scope="session")
def engine():
    test_engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)

    import app.core.database as database_module

    database_module.engine = test_engine
    database_module.SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    yield test_engine
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")()

    for table in reversed(Base.metadata.sorted_tables):
        session.execute(delete(table))
    session.flush()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    test_app = create_test_app()

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app) as test_client:
        yield test_client
    test_app.dependency_overrides.clear()
