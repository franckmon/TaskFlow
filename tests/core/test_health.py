from unittest.mock import patch

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.health import check_database_health, get_health_payload


class TestCheckDatabaseHealth:
    def test_returns_true_when_select_one_succeeds(self, db_session: Session) -> None:
        assert check_database_health(db_session) is True

    def test_returns_false_when_database_query_fails(self, db_session: Session) -> None:
        with patch.object(
            db_session,
            "execute",
            side_effect=OperationalError("SELECT 1", {}, Exception("connection refused")),
        ):
            assert check_database_health(db_session) is False


class TestGetHealthPayload:
    def test_returns_ok_payload_when_database_is_available(self, db_session: Session) -> None:
        status_code, payload = get_health_payload(db_session)

        assert status_code == 200
        assert payload == {"status": "ok"}

    def test_returns_degraded_payload_when_database_is_unavailable(
        self,
        db_session: Session,
    ) -> None:
        with patch("app.core.health.check_database_health", return_value=False):
            status_code, payload = get_health_payload(db_session)

        assert status_code == 503
        assert payload == {"status": "degraded"}
