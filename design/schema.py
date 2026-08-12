"""JSON schema and validator for structured extraction output."""

from typing import Any

EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["event_type", "component", "parameters", "confidence", "parse_status"],
    "additionalProperties": False,
    "properties": {
        "event_type": {"type": "string"},
        "component": {"type": ["string", "null"]},
        "parameters": {"type": "object"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "parse_status": {"type": "string", "enum": ["success", "partial", "failed"]},
    },
}

_REQUIRED_KEYS = set(EXTRACTION_SCHEMA["required"])
_VALID_CONFIDENCE = {"high", "medium", "low"}
_VALID_PARSE_STATUS = {"success", "partial", "failed"}


def validate_extraction(data: dict[str, Any]) -> list[str]:
    """Validate *data* against EXTRACTION_SCHEMA without external dependencies.

    Returns a list of error description strings; an empty list means valid.
    """
    if not isinstance(data, dict):
        return ["output is not a JSON object"]

    errors: list[str] = []

    # Required keys
    for key in _REQUIRED_KEYS:
        if key not in data:
            errors.append(f"missing required field: {key!r}")

    # No extra keys
    extra = set(data.keys()) - _REQUIRED_KEYS
    if extra:
        errors.append(f"unexpected fields: {sorted(extra)}")

    # If missing keys, skip type checks to avoid KeyError noise
    if errors:
        return errors

    # event_type: must be string
    if not isinstance(data["event_type"], str):
        errors.append(f"event_type must be a string, got {type(data['event_type']).__name__}")

    # component: must be string or None
    if data["component"] is not None and not isinstance(data["component"], str):
        errors.append(f"component must be a string or null, got {type(data['component']).__name__}")

    # parameters: must be a dict
    if not isinstance(data["parameters"], dict):
        errors.append(f"parameters must be an object, got {type(data['parameters']).__name__}")

    # confidence: enum check
    if data["confidence"] not in _VALID_CONFIDENCE:
        errors.append(
            f"confidence {data['confidence']!r} is not one of {sorted(_VALID_CONFIDENCE)}"
        )

    # parse_status: enum check
    if data["parse_status"] not in _VALID_PARSE_STATUS:
        errors.append(
            f"parse_status {data['parse_status']!r} is not one of {sorted(_VALID_PARSE_STATUS)}"
        )

    return errors
