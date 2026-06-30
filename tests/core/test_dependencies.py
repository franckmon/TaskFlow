from unittest.mock import patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import get_current_user
from app.core.exceptions import UnauthorizedError


class TestGetCurrentUser:
    def test_raises_when_token_payload_has_no_subject(self, db_session) -> None:
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="token-without-subject",
        )

        with patch("app.core.dependencies.decode_access_token", return_value={"role": "admin"}):
            with pytest.raises(UnauthorizedError, match="Invalid authentication credentials"):
                get_current_user(credentials, db_session)
