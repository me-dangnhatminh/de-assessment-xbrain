from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pipeline.__main__ import main
from pipeline.ingest import canonical_record_digest, iter_source_lines, parse_json_line
from pipeline.models import Disposition
from pipeline.validation import choose_final_action, validate_record

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPOSITORY_ROOT / "docs/onboard/datapack/data/app_logs_7days.jsonl"


def issue_codes(issues: tuple[object, ...]) -> set[str]:
    return {issue.issue_code for issue in issues}  # type: ignore[attr-defined]


def valid_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "timestamp": "2026-07-27T00:02:47Z",
        "service": "notification-worker",
        "level": "INFO",
        "message": "Heartbeat ok",
        "request_id": "req-1",
    }
    record.update(overrides)
    return record


def test_malformed_json_has_a_rejecting_provenance_envelope(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    raw_line = '{"timestamp": "broken"\n'
    source.write_text(raw_line, encoding="utf-8")

    envelope = next(iter_source_lines(source))
    record, issues = parse_json_line(envelope)

    assert record is None
    assert envelope.source_line == 1
    assert envelope.raw_line == raw_line.rstrip("\n")
    assert issue_codes(issues) == {"JSON_MALFORMED"}
    assert choose_final_action(issues) is Disposition.REJECT


def test_lines_are_enveloped_before_parse_and_bounded_by_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    source.write_bytes(b'{"ok": true}\n' + b"x" * 17 + b"\n")

    envelopes = list(iter_source_lines(source, max_line_bytes=16))

    assert [envelope.source_line for envelope in envelopes] == [1, 2]
    assert all(envelope.source_path == str(source.resolve()) for envelope in envelopes)
    assert all(envelope.source_sha256 == hashlib.sha256(source.read_bytes()).hexdigest() for envelope in envelopes)
    _, oversized_issues = parse_json_line(envelopes[1])
    assert issue_codes(oversized_issues) == {"LINE_TOO_LARGE"}


def test_required_types_timestamps_levels_and_content_have_stable_issues() -> None:
    record = valid_record(
        timestamp="2026-07-27T00:02:47",
        service="",
        level="DEBUG",
        message=7,
        request_id=None,
    )

    issues = validate_record(record)

    assert issue_codes(issues) == {
        "REQUIRED_FIELD_EMPTY",
        "REQUIRED_FIELD_TYPE",
        "TIMESTAMP_OFFSET_MISSING",
        "LEVEL_UNKNOWN",
    }
    assert choose_final_action(issues) is Disposition.REJECT


def test_unknown_service_is_valid_trace_id_is_optional_and_extra_fields_are_visible() -> None:
    record = valid_record(
        service="future-service",
        trace_id="trace-1",
        deployment="canary",
    )

    issues = validate_record(record)

    assert issue_codes(issues) == {"UNEXPECTED_FIELD"}
    assert issues[0].field == "deployment"
    assert choose_final_action(issues) is Disposition.ACCEPT
    assert canonical_record_digest(record) == canonical_record_digest(dict(reversed(record.items())))


def test_validate_streams_real_source_into_one_ordered_ledger_record_per_line(tmp_path: Path) -> None:
    source_before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    output_root = tmp_path / "validation"

    assert main(["validate", "--input", str(SOURCE), "--output-root", str(output_root)]) == 0

    ledger = [
        json.loads(line)
        for line in (output_root / "quality_ledger.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [entry["source_line"] for entry in ledger] == list(range(1, len(ledger) + 1))
    assert len(ledger) == sum(1 for _ in SOURCE.open(encoding="utf-8"))
    assert ledger[38]["issues"][0]["issue_code"] == "JSON_MALFORMED"
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_before
