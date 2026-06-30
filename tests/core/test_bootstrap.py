from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.bootstrap import ensure_default_admin
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.domain.user_types import UserRole
from app.models.user import User


@pytest.fixture
def clean_bootstrap_users(engine):
    session = sessionmaker(bind=engine)()
    session.execute(delete(User))
    session.commit()
    session.close()


class TestEnsureDefaultAdmin:
    def test_creates_admin_when_missing(self, db_session) -> None:
        created = ensure_default_admin(db_session)

        assert created is True
        admin = (
            db_session.query(User).filter(User.username == settings.BOOTSTRAP_ADMIN_USERNAME).one()
        )
        assert admin.role == UserRole.ADMIN
        assert verify_password(settings.BOOTSTRAP_ADMIN_PASSWORD, admin.hashed_password)

    def test_is_idempotent_when_admin_exists(self, db_session) -> None:
        db_session.add(
            User(
                username=settings.BOOTSTRAP_ADMIN_USERNAME,
                hashed_password=get_password_hash(settings.BOOTSTRAP_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
            )
        )
        db_session.flush()

        created = ensure_default_admin(db_session)

        assert created is False
        admins = (
            db_session.query(User).filter(User.username == settings.BOOTSTRAP_ADMIN_USERNAME).all()
        )
        assert len(admins) == 1

    def test_returns_false_and_rolls_back_on_flush_integrity_error(self) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.flush.side_effect = IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed"))

        created = ensure_default_admin(db)

        assert created is False
        db.rollback.assert_called_once()

    def test_skips_bootstrap_in_production(self, db_session) -> None:
        with patch.object(settings, "ENVIRONMENT", "production"):
            created = ensure_default_admin(db_session)

        assert created is False
        assert db_session.query(User).count() == 0

    def test_concurrent_bootstrap_creates_single_admin(
        self,
        engine,
        clean_bootstrap_users,
    ) -> None:
        session_factory = sessionmaker(bind=engine)
        first = session_factory()
        second = session_factory()

        try:
            created_first = ensure_default_admin(first)
            created_second = ensure_default_admin(second)

            assert created_first is True

            first.commit()
            if created_second:
                try:
                    second.commit()
                except IntegrityError:
                    second.rollback()

            verification = session_factory()
            admins = (
                verification.query(User)
                .filter(User.username == settings.BOOTSTRAP_ADMIN_USERNAME)
                .all()
            )
            assert len(admins) == 1
        finally:
            first.close()
            second.close()
