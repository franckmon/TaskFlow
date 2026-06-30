import pytest
from sqlalchemy.orm import Session

from app.domain.user_types import UserRole
from app.repositories.user_repository import UserRepository


@pytest.fixture
def user_repository(db_session: Session) -> UserRepository:
    return UserRepository(db_session)


class TestUserRepositoryCrud:
    def test_create_and_get(self, user_repository: UserRepository) -> None:
        created = user_repository.create(
            username="alice",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        stored = user_repository.get(created.id)

        assert stored is not None
        assert stored.username == "alice"
        assert stored.role == UserRole.USER

    def test_get_by_username(self, user_repository: UserRepository) -> None:
        user_repository.create(
            username="bob",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        found = user_repository.get_by_username("bob")

        assert found is not None
        assert found.role == UserRole.ADMIN

    def test_update(self, user_repository: UserRepository) -> None:
        created = user_repository.create(
            username="carol",
            hashed_password="old-hash",
            role=UserRole.USER,
        )

        updated = user_repository.update(
            created.id,
            hashed_password="new-hash",
            role=UserRole.ADMIN,
        )

        assert updated is not None
        assert updated.hashed_password == "new-hash"
        assert updated.role == UserRole.ADMIN

    def test_delete(self, user_repository: UserRepository) -> None:
        created = user_repository.create(
            username="dave",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        assert user_repository.delete(created.id) is True
        assert user_repository.get(created.id) is None

    def test_get_all_pagination(self, user_repository: UserRepository) -> None:
        for index in range(4):
            user_repository.create(
                username=f"user{index}",
                hashed_password="hashed",
                role=UserRole.USER,
            )

        page = user_repository.get_all(skip=1, limit=2)

        assert len(page) == 2
        assert [user.username for user in page] == ["user1", "user2"]
