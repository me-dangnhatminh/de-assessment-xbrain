"""Behavioral contracts for Phase 1 analytical normalization and writers."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import duckdb
import pytest

from pipeline.__main__ import main
from pipeline.integrity import (
    SourceIntegrityError,
    assert_source_unchanged,
    inventory_supplied_inputs,
    validate_output_root,
)
from pipeline.normalize import normalize_error, normalize_timestamp
from pipeline.write_outputs import (
    CLEAN_RECORD_SCHEMA,
    write_csv_atomic,
    write_json_atomic,
    write_jsonl_atomic,
    write_parquet_atomic,
    write_schema,
)


def sha256_file(path: Path) -> str:
    """Return a digest for deterministic-output assertions."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_normalize_timestamp_preserves_raw_offset_and_derives_utc_date() -> None:
    """Equivalent Z and offset instants keep provenance while deriving UTC."""
    z_timestamp = normalize_timestamp("2026-07-27T00:02:47Z")
    offset_timestamp = normalize_timestamp("2026-07-27T07:02:47+07:00")

    assert z_timestamp.timestamp_utc.isoformat() == "2026-07-27T00:02:47+00:00"
    assert offset_timestamp.timestamp_utc == z_timestamp.timestamp_utc
    assert z_timestamp.event_date_utc.isoformat() == "2026-07-27"
    assert offset_timestamp.event_date_utc == z_timestamp.event_date_utc
    assert z_timestamp.timestamp_offset_raw == "Z"
    assert offset_timestamp.timestamp_offset_raw == "+07:00"


def test_normalize_error_assigns_stable_primary_types_and_secondary_values() -> None:
    """Known error signatures retain structured detail without fragmenting ranks."""
    cases = {
        "ERR SMTPConnRefused host=mail-gw": "SMTP_CONN_REFUSED",
        "ERR PaymentDeclined code=DECLINED component=issuer": "PAYMENT_DECLINED",
        "ERR ConnTimeout component=core-api path=/v1/payments": "CONNECTION_TIMEOUT",
        "ERR NullPointer component=ledger": "NULL_POINTER",
        "HTTP 502 path=/payments/submit": "HTTP_502",
    }

    for message, expected_type in cases.items():
        normalized = normalize_error(message, "ERROR")
        assert normalized.error_type == expected_type

    detailed = normalize_error(
        "ERR PaymentDeclined code=DECLINED component=issuer path=/payments", "ERROR"
    )
    assert detailed.error_code == "DECLINED"
    assert detailed.related_component == "issuer"
    assert detailed.path == "/payments"
    assert json.loads(detailed.error_parameters_json) == {
        "code": "DECLINED",
        "component": "issuer",
        "path": "/payments",
    }


def test_normalize_error_keeps_unclassified_errors_and_omits_non_error_taxonomy() -> None:
    """Valid unmatched errors stay analytical; INFO/WARN have no taxonomy."""
    unmatched = normalize_error("Connection destabilized near queue boundary", "ERROR")
    info = normalize_error("Request completed", "INFO")
    warning = normalize_error("Queue depth rising", "WARN")

    assert unmatched.error_type == "UNCLASSIFIED_ERROR"
    assert unmatched.error_parameters_json == "{}"
    for normalized in (info, warning):
        assert normalized.error_type is None
        assert normalized.error_code is None
        assert normalized.related_component is None
        assert normalized.path is None
        assert normalized.error_parameters_json == "{}"


def test_atomic_writers_emit_fixed_schema_and_stable_bytes(tmp_path: Path) -> None:
    """Ordered values produce atomically replaced, deterministic evidence artifacts."""
    records = [
        {
            "source_line": 2,
            "source_sha256": "b" * 64,
            "timestamp_raw": "2026-07-27T00:02:47Z",
            "timestamp_utc": "2026-07-27T00:02:47+00:00",
            "event_date_utc": "2026-07-27",
            "timestamp_offset_raw": "Z",
            "service": "payment-api",
            "level": "ERROR",
            "message_raw": "HTTP 502 path=/payments",
            "request_id": "request-2",
            "trace_id": None,
            "error_type": "HTTP_502",
            "error_code": None,
            "related_component": None,
            "path": "/payments",
            "error_parameters_json": '{"path":"/payments"}',
        },
        {
            "source_line": 1,
            "source_sha256": "a" * 64,
            "timestamp_raw": "2026-07-27T07:02:47+07:00",
            "timestamp_utc": "2026-07-27T00:02:47+00:00",
            "event_date_utc": "2026-07-27",
            "timestamp_offset_raw": "+07:00",
            "service": "payment-api",
            "level": "INFO",
            "message_raw": "Request completed",
            "request_id": "request-1",
            "trace_id": "trace-1",
            "error_type": None,
            "error_code": None,
            "related_component": None,
            "path": None,
            "error_parameters_json": None,
        },
    ]
    json_path = tmp_path / "manifest.json"
    jsonl_path = tmp_path / "ledger.jsonl"
    csv_path = tmp_path / "table.csv"
    schema_path = tmp_path / "schema.json"
    parquet_path = tmp_path / "logs.parquet"

    write_json_atomic(json_path, {"z": 1, "a": 2})
    write_jsonl_atomic(jsonl_path, [{"line": 2}, {"line": 1}])
    write_csv_atomic(csv_path, ["source_line", "service"], [[2, "payment-api"], [1, "payment-api"]])
    write_schema(schema_path)
    write_parquet_atomic(parquet_path, records)
    first_hashes = [
        sha256_file(path) for path in (json_path, jsonl_path, csv_path, schema_path, parquet_path)
    ]

    write_json_atomic(json_path, {"a": 2, "z": 1})
    write_jsonl_atomic(jsonl_path, [{"line": 2}, {"line": 1}])
    write_csv_atomic(csv_path, ["source_line", "service"], [[2, "payment-api"], [1, "payment-api"]])
    write_schema(schema_path)
    write_parquet_atomic(parquet_path, records)
    assert [
        sha256_file(path) for path in (json_path, jsonl_path, csv_path, schema_path, parquet_path)
    ] == first_hashes

    with duckdb.connect() as connection:
        rows = connection.execute(
            "SELECT source_line, event_date_utc, error_type FROM read_parquet(?) ORDER BY source_line",
            [str(parquet_path)],
        ).fetchall()
    assert [
        (source_line, str(event_date), error_type) for source_line, event_date, error_type in rows
    ] == [
        (1, "2026-07-27", None),
        (2, "2026-07-27", "HTTP_502"),
    ]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert [column["name"] for column in schema["columns"]] == [
        column.name for column in CLEAN_RECORD_SCHEMA
    ]


def test_integrity_inventory_is_sorted_and_rejects_supplied_output_roots(tmp_path: Path) -> None:
    """Every supplied regular file is hashed and generated output cannot alias inputs."""
    repository_root = Path(__file__).resolve().parents[2]
    supplied_root = repository_root / "docs/onboard"
    inventory_before = inventory_supplied_inputs(supplied_root)
    inventory_after = inventory_supplied_inputs(supplied_root)

    assert [entry["path"] for entry in inventory_before] == sorted(
        entry["path"] for entry in inventory_before
    )
    assert any(entry["path"] == "datapack/data/app_logs_7days.jsonl" for entry in inventory_before)
    assert_source_unchanged(inventory_before, inventory_after)
    with pytest.raises(SourceIntegrityError):
        validate_output_root(supplied_root / "generated")
    assert validate_output_root(tmp_path / "generated") == (tmp_path / "generated").resolve()


def test_full_run_reconciles_all_lines_and_keeps_rejects_out_of_parquet(tmp_path: Path) -> None:
    """The run stage publishes complete ledger, schema, manifest, and analytical Parquet."""
    repository_root = Path(__file__).resolve().parents[2]
    source = repository_root / "docs/onboard/datapack/data/app_logs_7days.jsonl"
    output_root = tmp_path / "run"

    assert main(["run", "--input", str(source), "--output-root", str(output_root)]) == 0
    ledger_path = output_root / "evidence/phase1/quality_ledger.jsonl"
    manifest_path = output_root / "evidence/phase1/source_manifest.json"
    schema_path = output_root / "evidence/phase1/schema.json"
    parquet_path = output_root / "processed/logs_clean.parquet"
    ledger = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    actions = [entry["final_action"] for entry in ledger]

    assert len(ledger) == sum(1 for _ in source.open(encoding="utf-8"))
    assert actions.count("ACCEPT") + actions.count("REPAIR") + actions.count("REJECT") == len(
        ledger
    )
    with duckdb.connect() as connection:
        parquet_rows = connection.execute(
            "SELECT count(*) FROM read_parquet(?)", [str(parquet_path)]
        ).fetchone()[0]
        date_bounds = connection.execute(
            "SELECT min(event_date_utc), max(event_date_utc) FROM read_parquet(?)",
            [str(parquet_path)],
        ).fetchone()
    assert parquet_rows == actions.count("ACCEPT") + actions.count("REPAIR")
    assert date_bounds == (date(2026, 7, 27), date(2026, 8, 2))
    assert manifest_path.is_file()
    assert schema_path.is_file()


def test_full_run_is_stable_across_fresh_roots_and_integrity_command_reports_totals(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Fresh runs have byte-identical artifacts and independent integrity reporting."""
    repository_root = Path(__file__).resolve().parents[2]
    source = repository_root / "docs/onboard/datapack/data/app_logs_7days.jsonl"
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"

    assert main(["run", "--input", str(source), "--output-root", str(first_root)]) == 0
    assert main(["run", "--input", str(source), "--output-root", str(second_root)]) == 0
    paths = [
        "processed/logs_clean.parquet",
        "evidence/phase1/source_manifest.json",
        "evidence/phase1/quality_ledger.jsonl",
        "evidence/phase1/schema.json",
    ]
    assert {path: sha256_file(first_root / path) for path in paths} == {
        path: sha256_file(second_root / path) for path in paths
    }

    assert main(["integrity", "--input", str(source)]) == 0
    captured = capsys.readouterr()
    assert "files=" in captured.out
    assert "sha256=" in captured.out
    assert "final_actions" in captured.out
    assert "unclassified_errors=" in captured.out
