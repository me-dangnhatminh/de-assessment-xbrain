"""Fixed extraction test cases for the Bedrock trial."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TestCase:
    case_id: str
    message: str
    expected: dict[str, Any]
    note: str


CASES: tuple[TestCase, ...] = (
    TestCase(
        case_id="tc01",
        message="ERR ConnTimeout db-primary after 30s retry=3",
        expected={
            "event_type": "CONNECTION_TIMEOUT",
            "component": "db-primary",
            "parameters": {"retry": "3"},
            "confidence": "high",
            "parse_status": "success",
        },
        note="Clear ERROR: named component + retry parameter; matches normalize.py CONNECTION_TIMEOUT",
    ),
    TestCase(
        case_id="tc02",
        message="ERR PaymentDeclined txn=t811163 code=51",
        expected={
            "event_type": "PAYMENT_DECLINED",
            "component": None,
            "parameters": {"txn": "t811163", "code": "51"},
            "confidence": "high",
            "parse_status": "success",
        },
        note="Clear ERROR: transaction ID + decline code; component is null — no component token in message",
    ),
    TestCase(
        case_id="tc03",
        message="Report row mismatch expected=843 got=759",
        expected={
            "event_type": "DATA_MISMATCH",
            "component": None,
            "parameters": {"expected": "843", "got": "759"},
            "confidence": "high",
            "parse_status": "success",
        },
        note="WARN-class message: no ERR prefix; test that model handles non-ERROR levels correctly",
    ),
    TestCase(
        case_id="tc04",
        message="Retry 1/3 calling notification-worker",
        expected={
            "event_type": "RETRY",
            "component": "notification-worker",
            "parameters": {"attempt": "1", "max_attempts": "3"},
            "confidence": "medium",
            "parse_status": "partial",
        },
        note="Ambiguous: no ERR token; fraction 1/3 requires splitting; underlying error reason absent — partial parse",
    ),
    TestCase(
        case_id="tc05",
        message="Heartbeat ok",
        expected={
            "event_type": "HEARTBEAT",
            "component": None,
            "parameters": {},
            "confidence": "low",
            "parse_status": "partial",
        },
        note="Edge case: minimal message, no parameters, no level field in source record; tests no-fabrication rule",
    ),
)
