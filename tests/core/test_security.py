from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHelpers:
    def test_hash_and_verify_matching_password(self) -> None:
        hashed = get_password_hash("secret-password")

        assert hashed != "secret-password"
        assert verify_password("secret-password", hashed)

    def test_verify_rejects_wrong_password(self) -> None:
        hashed = get_password_hash("secret-password")

        assert not verify_password("wrong-password", hashed)


class TestAccessTokenHelpers:
    def test_create_and_decode_roundtrip(self) -> None:
        token = create_access_token({"sub": "alice", "role": "admin"})

        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == "alice"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_uses_custom_expiration(self) -> None:
        expires_delta = timedelta(minutes=5)
        before = datetime.now(UTC)

        token = create_access_token({"sub": "bob"}, expires_delta=expires_delta)
        payload = decode_access_token(token)

        assert payload is not None
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert exp >= before + expires_delta - timedelta(seconds=1)

    def test_decode_returns_none_for_invalid_token(self) -> None:
        assert decode_access_token("not-a-valid-token") is None

    def test_decode_returns_none_for_expired_token(self) -> None:
        token = create_access_token({"sub": "alice"}, expires_delta=timedelta(seconds=-1))

        assert decode_access_token(token) is None

    def test_decode_returns_none_for_tampered_token(self) -> None:
        token = create_access_token({"sub": "alice"})
        tampered = f"{token}invalid"

        assert decode_access_token(tampered) is None

    def test_decode_returns_none_for_wrong_secret(self) -> None:
        token = jwt.encode(
            {"sub": "alice", "exp": datetime.now(UTC) + timedelta(minutes=5)},
            "wrong-secret",
            algorithm=settings.ALGORITHM,
        )

        assert decode_access_token(token) is None
