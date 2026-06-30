from unittest.mock import MagicMock, patch

from app.core.database import get_db


class TestGetDb:
    @patch("app.core.database.SessionLocal")
    def test_yields_session_and_closes_it_in_finally_block(self, mock_session_local) -> None:
        session = MagicMock()
        mock_session_local.return_value = session
        generator = get_db()

        yielded = next(generator)
        generator.close()

        assert yielded is session
        session.close.assert_called_once()
