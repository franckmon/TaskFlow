import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import get_password_hash
from app.domain.user_types import UserRole
from app.models.user import User


@pytest.fixture
def seed_admin(db_session) -> User:
    admin = User(
        username=settings.BOOTSTRAP_ADMIN_USERNAME,
        hashed_password=get_password_hash(settings.BOOTSTRAP_ADMIN_PASSWORD),
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.flush()
    return admin


@pytest.fixture
def admin_credentials() -> dict[str, str]:
    return {
        "username": settings.BOOTSTRAP_ADMIN_USERNAME,
        "password": settings.BOOTSTRAP_ADMIN_PASSWORD,
    }


@pytest.fixture
def regular_user(db_session) -> User:
    user = User(
        username="regular",
        hashed_password=get_password_hash("userpassword"),
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def regular_credentials(regular_user: User) -> dict[str, str]:
    return {
        "username": regular_user.username,
        "password": "userpassword",
    }


def login(client: TestClient, credentials: dict[str, str]) -> dict[str, str]:
    response = client.post("/auth/login", json=credentials)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(
    client: TestClient,
    seed_admin: User,
    admin_credentials: dict[str, str],
) -> dict[str, str]:
    return login(client, admin_credentials)


@pytest.fixture
def user_headers(
    client: TestClient,
    regular_credentials: dict[str, str],
) -> dict[str, str]:
    return login(client, regular_credentials)


def create_task_via_api(
    client: TestClient,
    headers: dict[str, str],
    *,
    title: str = "Integration task",
    description: str | None = "Task description",
    status: str = "new",
    priority: str = "normal",
) -> dict:
    response = client.post(
        "/tasks/",
        headers=headers,
        json={
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
        },
    )
    assert response.status_code == 200
    return response.json()
