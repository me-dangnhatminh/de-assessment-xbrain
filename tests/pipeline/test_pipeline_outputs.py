"""Behavioral contracts for Phase 1 analytical normalization and writers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb

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
        assert normalized.error_parameters_json is None


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
    first_hashes = [sha256_file(path) for path in (json_path, jsonl_path, csv_path, schema_path, parquet_path)]

    write_json_atomic(json_path, {"a": 2, "z": 1})
    write_jsonl_atomic(jsonl_path, [{"line": 2}, {"line": 1}])
    write_csv_atomic(csv_path, ["source_line", "service"], [[2, "payment-api"], [1, "payment-api"]])
    write_schema(schema_path)
    write_parquet_atomic(parquet_path, records)
    assert [sha256_file(path) for path in (json_path, jsonl_path, csv_path, schema_path, parquet_path)] == first_hashes

    with duckdb.connect() as connection:
        rows = connection.execute(
            "SELECT source_line, event_date_utc, error_type FROM read_parquet(?) ORDER BY source_line",
            [str(parquet_path)],
        ).fetchall()
    assert rows == [(1, "2026-07-27", None), (2, "2026-07-27", "HTTP_502")]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert [column["name"] for column in schema["columns"]] == [column.name for column in CLEAN_RECORD_SCHEMA]
