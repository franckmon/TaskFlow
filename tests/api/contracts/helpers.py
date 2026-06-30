from typing import Any

import pytest
from httpx import Response
from pydantic import BaseModel, TypeAdapter, ValidationError


def assert_response_schema(
    response: Response,
    schema: Any,
    *,
    status_code: int = 200,
) -> Any:
    """
    Validate an HTTP response body against a Pydantic model or type adapter schema.

    Fails when required fields are missing or renamed.
    """
    assert response.status_code == status_code, (
        f"Expected HTTP {status_code}, got {response.status_code}: {response.text}"
    )

    payload = response.json()
    adapter = TypeAdapter(schema)

    try:
        return adapter.validate_python(payload)
    except ValidationError as exc:
        schema_name = getattr(schema, "__name__", repr(schema))
        pytest.fail(f"Response contract mismatch for {schema_name}:\npayload={payload!r}\n{exc}")


def assert_model_fields(model: BaseModel, expected_fields: set[str]) -> None:
    """Guard against silent removal of documented response fields."""
    actual_fields = set(type(model).model_fields.keys())
    missing = expected_fields - actual_fields
    if missing:
        pytest.fail(f"Contract schema is missing expected fields: {sorted(missing)}")
