"""Typed contracts shared by the auditable validation pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Disposition(str, Enum):
    """The one record-level action selected after all issues are collected."""

    ACCEPT = "ACCEPT"
    REPAIR = "REPAIR"
    REJECT = "REJECT"


@dataclass(frozen=True)
class Issue:
    """A stable, source-grounded validation observation."""

    issue_code: str
    field: str | None
    original_value: Any
    normalized_value: Any
    action: Disposition
    reason: str

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["action"] = self.action.value
        return value


@dataclass(frozen=True)
class Normalization:
    """A representation-preserving transformation, distinct from repair."""

    field: str
    original_value: Any
    normalized_value: Any
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceEnvelope:
    """Immutable provenance assigned before decoding or JSON parsing."""

    source_path: str
    source_sha256: str
    source_line: int
    raw_line: str
    preparse_issues: tuple[Issue, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LedgerEntry:
    """One ordered audit record for one physical source line."""

    source_path: str
    source_sha256: str
    source_line: int
    record_digest: str | None
    raw_line: str
    issues: tuple[Issue, ...]
    normalizations: tuple[Normalization, ...]
    final_action: Disposition
    retained_source_line: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "source_line": self.source_line,
            "record_digest": self.record_digest,
            "raw_line": self.raw_line,
            "issues": [issue.as_dict() for issue in self.issues],
            "normalizations": [normalization.as_dict() for normalization in self.normalizations],
            "final_action": self.final_action.value,
            "retained_source_line": self.retained_source_line,
        }


@dataclass(frozen=True)
class CleanRecord:
    """The fixed analytical-row contract for later normalization and Parquet writing."""

    source_line: int
    source_sha256: str
    timestamp_raw: str
    timestamp_utc: str
    event_date_utc: str
    timestamp_offset_raw: str
    service: str
    level: str
    message_raw: str
    request_id: str
    trace_id: str | None
    error_type: str | None
    error_code: str | None
    related_component: str | None
    path: str | None
    error_parameters_json: str
