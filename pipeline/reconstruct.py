"""Deterministic reconstruction of ledger and Parquet evidence from immutable input."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from pipeline.ingest import canonical_record_digest, iter_source_lines, parse_json_line
from pipeline.models import CleanRecord, Disposition, LedgerEntry, Normalization
from pipeline.normalize import normalize_error, normalize_timestamp
from pipeline.validation import choose_final_action, make_issue, validate_record


def reconstruct_evidence(
    input_path: Path, max_line_bytes: int
) -> tuple[list[LedgerEntry], list[dict[str, Any]]]:
    """Validate every physical line and normalize only analytical final actions.

    This is the single production validation/normalization stream: run, trace,
    and manifest verification all derive their evidence from it, so a reviewer
    can prove every reported row was produced from the same source bytes and
    the same rules.
    """
    ledger_entries: list[LedgerEntry] = []
    clean_records: list[dict[str, Any]] = []
    first_source_line_by_digest: dict[str, int] = {}
    for envelope in iter_source_lines(input_path, max_line_bytes):
        record, issues = parse_json_line(envelope)
        if record is not None:
            issues = (*issues, *validate_record(record))
            record_digest = canonical_record_digest(record)
        else:
            record_digest = None
        final_action = choose_final_action(issues)
        retained_source_line = None
        if record is not None and final_action in {Disposition.ACCEPT, Disposition.REPAIR}:
            # Only retained (analytical) rows can be the cross-reference target of
            # an exact duplicate; a rejected first occurrence is not retained.
            retained_source_line = first_source_line_by_digest.setdefault(
                record_digest, envelope.source_line
            )
            if retained_source_line != envelope.source_line:
                issues = (
                    *issues,
                    make_issue("EXACT_DUPLICATE", None, record_digest, retained_source_line),
                )
                final_action = choose_final_action(issues)
        normalizations: tuple[Normalization, ...] = ()
        if record is not None and final_action in {Disposition.ACCEPT, Disposition.REPAIR}:
            timestamp = normalize_timestamp(record["timestamp"])
            error = normalize_error(record["message"], record["level"])
            normalizations = (timestamp.evidence,)
            if record["level"] == "ERROR":
                normalizations += (
                    Normalization(
                        field="error_type",
                        original_value=record["message"],
                        normalized_value=error.error_type,
                        reason="explicit ERROR signature taxonomy; raw message is retained",
                    ),
                )
            clean_records.append(
                asdict(
                    CleanRecord(
                        source_line=envelope.source_line,
                        source_sha256=envelope.source_sha256,
                        timestamp_raw=record["timestamp"],
                        timestamp_utc=timestamp.timestamp_utc.isoformat(),
                        event_date_utc=timestamp.event_date_utc.isoformat(),
                        timestamp_offset_raw=timestamp.timestamp_offset_raw,
                        service=record["service"],
                        level=record["level"],
                        message_raw=record["message"],
                        request_id=record["request_id"],
                        trace_id=record.get("trace_id"),
                        error_type=error.error_type,
                        error_code=error.error_code,
                        related_component=error.related_component,
                        path=error.path,
                        error_parameters_json=error.error_parameters_json,
                    )
                )
            )
        ledger_entries.append(
            LedgerEntry(
                source_path=envelope.source_path,
                source_sha256=envelope.source_sha256,
                source_line=envelope.source_line,
                record_digest=record_digest,
                raw_line=envelope.raw_line,
                issues=issues,
                normalizations=normalizations,
                final_action=final_action,
                retained_source_line=retained_source_line,
            )
        )
    return ledger_entries, clean_records
