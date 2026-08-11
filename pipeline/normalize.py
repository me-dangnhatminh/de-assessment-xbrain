"""Deterministic UTC and ERROR-message normalization for analytical rows."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime

from pipeline.models import Normalization


@dataclass(frozen=True)
class NormalizedTimestamp:
    """A provenance-preserving UTC representation of a valid timestamp."""

    timestamp_utc: datetime
    event_date_utc: date
    timestamp_offset_raw: str
    evidence: Normalization


@dataclass(frozen=True)
class NormalizedError:
    """Stable ERROR taxonomy plus secondary details retained for analysis."""

    error_type: str | None
    error_code: str | None
    related_component: str | None
    path: str | None
    error_parameters_json: str


_ERROR_TYPES = {
    "SMTPConnRefused": "SMTP_CONN_REFUSED",
    "PaymentDeclined": "PAYMENT_DECLINED",
    "ConnTimeout": "CONNECTION_TIMEOUT",
    "NullPointer": "NULL_POINTER",
}
_ERROR_TOKEN = re.compile(r"^ERR\s+(?P<token>[A-Za-z][A-Za-z0-9_]*)\b\s*(?P<details>.*)$")
_HTTP_502 = re.compile(r"\bHTTP\s+502\b\s*(?P<details>.*)$")
_PARAMETER = re.compile(r"(?P<key>[A-Za-z][A-Za-z0-9_]*)=(?P<value>[^\s]+)")


def normalize_timestamp(timestamp_raw: str) -> NormalizedTimestamp:
    """Convert one already-validated aware timestamp to UTC without calling it a repair."""
    parsed = datetime.fromisoformat(timestamp_raw)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an offset")
    timestamp_utc = parsed.astimezone(UTC)
    offset_raw = "Z" if timestamp_raw.endswith("Z") else timestamp_raw[-6:]
    return NormalizedTimestamp(
        timestamp_utc=timestamp_utc,
        event_date_utc=timestamp_utc.date(),
        timestamp_offset_raw=offset_raw,
        evidence=Normalization(
            field="timestamp",
            original_value=timestamp_raw,
            normalized_value=timestamp_utc.isoformat(),
            reason="valid aware timestamp represented as the same UTC instant",
        ),
    )


def _details_to_parameters(details: str) -> dict[str, str]:
    """Extract only explicit key/value values so raw messages remain authoritative."""
    return {match.group("key"): match.group("value") for match in _PARAMETER.finditer(details)}


def normalize_error(message_raw: str, level: str) -> NormalizedError:
    """Classify ERROR rows only, preserving unmatched valid errors for review."""
    if level != "ERROR":
        return NormalizedError(None, None, None, None, "{}")

    token_match = _ERROR_TOKEN.match(message_raw)
    http_match = _HTTP_502.search(message_raw)
    if token_match is not None and token_match.group("token") in _ERROR_TYPES:
        error_type = _ERROR_TYPES[token_match.group("token")]
        parameters = _details_to_parameters(token_match.group("details"))
    elif http_match is not None:
        error_type = "HTTP_502"
        parameters = _details_to_parameters(http_match.group("details"))
    else:
        error_type = "UNCLASSIFIED_ERROR"
        parameters = {}

    return NormalizedError(
        error_type=error_type,
        error_code=parameters.get("code"),
        related_component=parameters.get("component"),
        path=parameters.get("path"),
        error_parameters_json=json.dumps(
            parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
    )
