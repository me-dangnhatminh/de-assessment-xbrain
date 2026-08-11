"""Explicit validation policies and disposition precedence for parsed log records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pipeline.models import Disposition, Issue

REQUIRED_FIELDS = ("timestamp", "service", "level", "message", "request_id")
ALLOWED_LEVELS = frozenset({"INFO", "WARN", "ERROR"})
OPTIONAL_FIELDS = frozenset({"trace_id"})


@dataclass(frozen=True)
class IssuePolicy:
    """Stable English policy metadata used to construct deterministic issue entries."""

    action: Disposition
    reason: str


ISSUE_POLICIES = {
    "REQUIRED_FIELD_MISSING": IssuePolicy(
        Disposition.REJECT, "required analytical field is missing"
    ),
    "REQUIRED_FIELD_TYPE": IssuePolicy(
        Disposition.REJECT, "required analytical field must be a string"
    ),
    "REQUIRED_FIELD_EMPTY": IssuePolicy(
        Disposition.REJECT, "required analytical field must not be empty"
    ),
    "TIMESTAMP_INVALID": IssuePolicy(Disposition.REJECT, "timestamp is not ISO 8601"),
    "TIMESTAMP_OFFSET_MISSING": IssuePolicy(
        Disposition.REJECT, "timestamp must include a UTC offset or Z suffix"
    ),
    "LEVEL_UNKNOWN": IssuePolicy(
        Disposition.REJECT, "level must be one of INFO, WARN, or ERROR for this fixed POC"
    ),
    "TRACE_ID_TYPE": IssuePolicy(
        Disposition.REJECT, "optional trace_id must be a non-empty string"
    ),
    "UNEXPECTED_FIELD": IssuePolicy(
        Disposition.ACCEPT,
        "unexpected field is retained in raw provenance but ignored analytically",
    ),
    "SYNTHETIC_REPAIR": IssuePolicy(
        Disposition.REPAIR,
        "synthetic test-only example of a lossless, unambiguous, mechanically provable repair",
    ),
}


def make_issue(
    issue_code: str,
    field: str | None,
    original_value: Any,
    normalized_value: Any = None,
) -> Issue:
    """Build an issue from the stable catalogue without hidden default actions."""
    policy = ISSUE_POLICIES[issue_code]
    return Issue(
        issue_code=issue_code,
        field=field,
        original_value=original_value,
        normalized_value=normalized_value,
        action=policy.action,
        reason=policy.reason,
    )


def _timestamp_issues(timestamp: str) -> list[Issue]:
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return [make_issue("TIMESTAMP_INVALID", "timestamp", timestamp)]
    if parsed.tzinfo is None:
        return [make_issue("TIMESTAMP_OFFSET_MISSING", "timestamp", timestamp)]
    return []


def validate_record(record: dict[str, Any]) -> tuple[Issue, ...]:
    """Collect every independently applicable issue in deterministic catalogue order."""
    issues: list[Issue] = []
    for field in REQUIRED_FIELDS:
        if field not in record or record[field] is None:
            issues.append(make_issue("REQUIRED_FIELD_MISSING", field, record.get(field)))
        elif not isinstance(record[field], str):
            issues.append(make_issue("REQUIRED_FIELD_TYPE", field, record[field]))
        elif not record[field]:
            issues.append(make_issue("REQUIRED_FIELD_EMPTY", field, record[field]))

    timestamp = record.get("timestamp")
    if isinstance(timestamp, str) and timestamp:
        issues.extend(_timestamp_issues(timestamp))

    level = record.get("level")
    if isinstance(level, str) and level and level not in ALLOWED_LEVELS:
        issues.append(make_issue("LEVEL_UNKNOWN", "level", level))

    if "trace_id" in record and record["trace_id"] is not None:
        trace_id = record["trace_id"]
        if not isinstance(trace_id, str) or not trace_id:
            issues.append(make_issue("TRACE_ID_TYPE", "trace_id", trace_id))

    for field in sorted(set(record) - set(REQUIRED_FIELDS) - OPTIONAL_FIELDS):
        issues.append(make_issue("UNEXPECTED_FIELD", field, record[field]))
    return tuple(issues)


def choose_final_action(issues: tuple[Issue, ...] | list[Issue]) -> Disposition:
    """Apply D-05 explicitly: REJECT overrides REPAIR, which overrides ACCEPT."""
    actions = {issue.action for issue in issues}
    if Disposition.REJECT in actions:
        return Disposition.REJECT
    if Disposition.REPAIR in actions:
        return Disposition.REPAIR
    return Disposition.ACCEPT
