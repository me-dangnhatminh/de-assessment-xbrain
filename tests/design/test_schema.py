"""Unit tests for design.schema.validate_extraction."""

from design.schema import validate_extraction


def _valid() -> dict:
    return {
        "event_type": "CONNECTION_TIMEOUT",
        "component": "db-primary",
        "parameters": {"retry": "3"},
        "confidence": "high",
        "parse_status": "success",
    }


def test_schema_valid_full_object() -> None:
    errors = validate_extraction(_valid())
    assert errors == []


def test_schema_rejects_missing_field() -> None:
    data = _valid()
    del data["event_type"]
    errors = validate_extraction(data)
    assert errors  # non-empty list


def test_schema_rejects_unknown_field() -> None:
    data = _valid()
    data["extra"] = "unexpected"
    errors = validate_extraction(data)
    assert errors


def test_schema_rejects_invalid_confidence_value() -> None:
    data = _valid()
    data["confidence"] = "very_high"
    errors = validate_extraction(data)
    assert errors


def test_schema_rejects_null_event_type() -> None:
    data = _valid()
    data["event_type"] = None
    errors = validate_extraction(data)
    assert errors
