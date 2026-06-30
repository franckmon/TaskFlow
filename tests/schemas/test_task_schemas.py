import pytest
from pydantic import ValidationError

from app.schemas.task import SEARCH_MAX_LENGTH, TaskListQuery


class TestTaskListQuery:
    def test_normalize_search_strips_whitespace(self) -> None:
        query = TaskListQuery(search="  billing  ")

        assert query.search == "billing"

    def test_normalize_search_rejects_whitespace_only(self) -> None:
        with pytest.raises(ValidationError, match="search cannot be empty"):
            TaskListQuery(search="   ")

    def test_normalize_search_passes_through_non_string_values(self) -> None:
        normalized = TaskListQuery.normalize_search(123)

        assert normalized == 123

    def test_validate_search_length_rejects_too_long_values(self) -> None:
        with pytest.raises(ValueError, match=f"at most {SEARCH_MAX_LENGTH}"):
            TaskListQuery.validate_search_length("x" * (SEARCH_MAX_LENGTH + 1))
