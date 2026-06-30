from types import SimpleNamespace

import pytest

from app.core.exceptions import PermissionDeniedError
from app.domain.task_ownership import (
    TASK_OWNERSHIP_SCOPE,
    TaskOwnershipContext,
    UserOwnershipContext,
    assert_task_access_allowed,
    is_task_access_allowed,
    normalize_actor_id,
    task_ownership_context_from_mapping,
    user_ownership_context_from_mapping,
)
from app.domain.user_types import UserRole


class TestOwnershipValidation:
    def test_owner_can_access_task(self) -> None:
        user = UserOwnershipContext(id=1, role=UserRole.USER)
        task = TaskOwnershipContext(owner_id=1)

        assert is_task_access_allowed(user, task) is True
        assert_task_access_allowed(user, task)

    def test_non_owner_is_denied(self) -> None:
        user = UserOwnershipContext(id=2, role=UserRole.USER)
        task = TaskOwnershipContext(owner_id=1)

        assert is_task_access_allowed(user, task) is False

        with pytest.raises(PermissionDeniedError, match="You do not have access to this task"):
            assert_task_access_allowed(user, task)


class TestRoleBasedOverride:
    @pytest.mark.parametrize(
        ("owner_id", "expected"),
        [
            (1, True),
            (42, True),
            (None, True),
        ],
    )
    def test_admin_can_access_any_task(self, owner_id: int | None, expected: bool) -> None:
        admin = UserOwnershipContext(id=99, role=UserRole.ADMIN)
        task = TaskOwnershipContext(owner_id=owner_id, invalid_owner=True)

        assert is_task_access_allowed(admin, task) is expected
        assert_task_access_allowed(admin, task)

    def test_non_admin_remains_restricted_to_owned_or_shared_tasks(self) -> None:
        user = UserOwnershipContext(id=2, role=UserRole.USER)

        assert is_task_access_allowed(user, TaskOwnershipContext(owner_id=1)) is False
        assert is_task_access_allowed(user, TaskOwnershipContext(owner_id=2)) is True
        assert is_task_access_allowed(user, TaskOwnershipContext(owner_id=None)) is True

    @pytest.mark.parametrize(
        ("role", "owner_id", "expected"),
        [
            (UserRole.USER, 1, False),
            (UserRole.ADMIN, 1, True),
            (UserRole.USER, 2, True),
            (UserRole.ADMIN, 2, True),
        ],
    )
    def test_admin_flag_transitions_change_access_for_foreign_task(
        self,
        role: UserRole,
        owner_id: int,
        expected: bool,
    ) -> None:
        user = UserOwnershipContext(id=2, role=role)
        task = TaskOwnershipContext(owner_id=owner_id)

        assert is_task_access_allowed(user, task) is expected


class TestMismatchedIdTypes:
    @pytest.mark.parametrize(
        ("user_id", "owner_id"),
        [
            ("1", 1),
            (1, "1"),
            ("42", "42"),
        ],
    )
    def test_string_and_int_ids_match_after_normalization(
        self,
        user_id: int | str,
        owner_id: int | str,
    ) -> None:
        user = UserOwnershipContext(id=user_id, role=UserRole.USER)
        task = TaskOwnershipContext(owner_id=owner_id)

        assert is_task_access_allowed(user, task) is True

    @pytest.mark.parametrize(
        ("user_id", "owner_id"),
        [
            ("1", 2),
            (1, "2"),
            ("2", 1),
        ],
    )
    def test_mismatched_normalized_ids_are_denied(
        self,
        user_id: int | str,
        owner_id: int | str,
    ) -> None:
        user = UserOwnershipContext(id=user_id, role=UserRole.USER)
        task = TaskOwnershipContext(owner_id=owner_id)

        assert is_task_access_allowed(user, task) is False

    @pytest.mark.parametrize(
        "value",
        [True, False, "abc", "1.5", [], {}],
    )
    def test_normalize_actor_id_rejects_non_numeric_values(self, value: object) -> None:
        assert normalize_actor_id(value) is None


class TestNoneAndMissingUser:
    def test_none_user_is_denied(self) -> None:
        task = TaskOwnershipContext(owner_id=1)

        assert is_task_access_allowed(None, task) is False

        with pytest.raises(PermissionDeniedError):
            assert_task_access_allowed(None, task)

    def test_none_user_mapping_returns_none(self) -> None:
        assert user_ownership_context_from_mapping(None) is None

    def test_missing_user_id_is_denied_even_for_shared_task(self) -> None:
        deleted_user = UserOwnershipContext(id=None, role=UserRole.USER)
        shared_task = TaskOwnershipContext(owner_id=None)

        assert is_task_access_allowed(deleted_user, shared_task) is False

        with pytest.raises(PermissionDeniedError):
            assert_task_access_allowed(deleted_user, shared_task)

    def test_user_mapping_without_id_denies_access(self) -> None:
        partial_user = SimpleNamespace(role=UserRole.USER)
        task = TaskOwnershipContext(owner_id=1)

        user = user_ownership_context_from_mapping(partial_user)

        assert user is not None
        assert user.id is None
        assert is_task_access_allowed(user, task) is False


class TestCorruptedTaskOwnership:
    @pytest.mark.parametrize(
        "raw_owner",
        [True, "owner", "1.0", [], {}],
    )
    def test_corrupted_owner_field_denies_non_admin(self, raw_owner: object) -> None:
        user = UserOwnershipContext(id=1, role=UserRole.USER)
        task = task_ownership_context_from_mapping(SimpleNamespace(owner_id=raw_owner))

        assert task.invalid_owner is True
        assert is_task_access_allowed(user, task) is False

        with pytest.raises(PermissionDeniedError):
            assert_task_access_allowed(user, task)

    def test_corrupted_owner_field_allows_admin(self) -> None:
        admin = UserOwnershipContext(id=5, role=UserRole.ADMIN)
        task = task_ownership_context_from_mapping(SimpleNamespace(owner_id="broken"))

        assert is_task_access_allowed(admin, task) is True

    def test_explicit_invalid_owner_flag_denies_non_admin(self) -> None:
        user = UserOwnershipContext(id=1, role=UserRole.USER)
        task = TaskOwnershipContext(owner_id=1, invalid_owner=True)

        assert is_task_access_allowed(user, task) is False

    def test_task_mapping_without_owner_treats_task_as_shared(self) -> None:
        user = UserOwnershipContext(id=3, role=UserRole.USER)
        task = task_ownership_context_from_mapping(SimpleNamespace())

        assert task.owner_id is None
        assert task.invalid_owner is False
        assert is_task_access_allowed(user, task) is True


class TestMappingEdgeCases:
    def test_user_mapping_defaults_missing_role_to_user(self) -> None:
        partial_user = SimpleNamespace(id=4)
        owned_by_other = TaskOwnershipContext(owner_id=1)

        user = user_ownership_context_from_mapping(partial_user)

        assert user is not None
        assert user.role == UserRole.USER
        assert is_task_access_allowed(user, owned_by_other) is False

    def test_user_mapping_rejects_invalid_role_value(self) -> None:
        partial_user = SimpleNamespace(id=4, role="admin")

        user = user_ownership_context_from_mapping(partial_user)

        assert user is not None
        assert user.role == UserRole.USER

    @pytest.mark.parametrize("raw_owner", ["7", 7])
    def test_task_mapping_preserves_valid_numeric_owner(self, raw_owner: int | str) -> None:
        task = task_ownership_context_from_mapping(SimpleNamespace(owner_id=raw_owner))

        assert task.invalid_owner is False
        assert normalize_actor_id(task.owner_id) == 7


class TestAssertTaskAccessAllowed:
    def test_assert_does_not_raise_when_access_allowed(self) -> None:
        user = UserOwnershipContext(id=1, role=UserRole.USER)
        task = TaskOwnershipContext(owner_id=None)

        assert_task_access_allowed(user, task)


class TestOwnershipScope:
    def test_workspace_scope_constant(self) -> None:
        assert TASK_OWNERSHIP_SCOPE == "global_shared_workspace"
