from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token
from tests.api.conftest import create_task_via_api, login
from tests.api.test_errors import assert_error

PROTECTED_ENDPOINTS = [
    ("get", "/auth/me", None),
    ("get", "/tasks/", None),
    ("post", "/tasks/", {"title": "Protected task", "status": "new", "priority": "normal"}),
]


def _bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _expired_token(*, username: str = "testadmin", role: str = "admin") -> str:
    return create_access_token(
        {"sub": username, "role": role},
        expires_delta=timedelta(seconds=-1),
    )


def _invalid_signature_token(*, username: str = "testadmin") -> str:
    return jwt.encode(
        {"sub": username, "exp": datetime.now(UTC) + timedelta(minutes=5)},
        "wrong-secret-key-for-signature-test",
        algorithm=settings.ALGORITHM,
    )


def _corrupted_token_after_logout(valid_token: str) -> str:
    """Simulate a client-side cleared/corrupted bearer after logout."""
    return f"{valid_token[:-12]}cleared-token"


class TestExpiredJwt:
    @pytest.mark.parametrize("method,path,json_body", PROTECTED_ENDPOINTS)
    def test_expired_jwt_returns_401(
        self,
        client: TestClient,
        seed_admin,
        method: str,
        path: str,
        json_body: dict | None,
    ) -> None:
        headers = _bearer_headers(_expired_token())

        response = client.request(method, path, headers=headers, json=json_body)

        assert_error(
            response,
            status_code=401,
            code="unauthorized",
            detail="Invalid authentication credentials",
        )


class TestInvalidJwtSignature:
    @pytest.mark.parametrize("method,path,json_body", PROTECTED_ENDPOINTS)
    def test_invalid_signature_jwt_returns_401(
        self,
        client: TestClient,
        seed_admin,
        method: str,
        path: str,
        json_body: dict | None,
    ) -> None:
        headers = _bearer_headers(_invalid_signature_token())

        response = client.request(method, path, headers=headers, json=json_body)

        assert_error(
            response,
            status_code=401,
            code="unauthorized",
            detail="Invalid authentication credentials",
        )


class TestAccessAfterLogout:
    @pytest.mark.parametrize("method,path,json_body", PROTECTED_ENDPOINTS)
    def test_corrupted_token_after_logout_returns_401(
        self,
        client: TestClient,
        seed_admin,
        admin_credentials: dict[str, str],
        method: str,
        path: str,
        json_body: dict | None,
    ) -> None:
        session_headers = login(client, admin_credentials)
        valid_token = session_headers["Authorization"].removeprefix("Bearer ")
        headers = _bearer_headers(_corrupted_token_after_logout(valid_token))

        response = client.request(method, path, headers=headers, json=json_body)

        assert_error(
            response,
            status_code=401,
            code="unauthorized",
            detail="Invalid authentication credentials",
        )


class TestDeletedUserToken:
    @pytest.mark.parametrize("method,path,json_body", PROTECTED_ENDPOINTS)
    def test_deleted_user_token_returns_401(
        self,
        client: TestClient,
        seed_admin,
        admin_headers: dict[str, str],
        db_session,
        method: str,
        path: str,
        json_body: dict | None,
    ) -> None:
        create_task_via_api(client, admin_headers, title="Task before user delete")
        db_session.delete(seed_admin)
        db_session.flush()

        response = client.request(method, path, headers=admin_headers, json=json_body)

        assert_error(
            response,
            status_code=401,
            code="unauthorized",
            detail="User not found",
        )
