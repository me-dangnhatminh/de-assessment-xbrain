"""Atomic, deterministic writers for reviewer-facing Phase 1 evidence."""

from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import duckdb


@dataclass(frozen=True)
class SchemaColumn:
    """One declared analytical column and its reviewer-facing provenance."""

    name: str
    duckdb_type: str
    nullable: bool
    description: str
    format: str | None = None


CLEAN_RECORD_SCHEMA = (
    SchemaColumn("source_line", "BIGINT", False, "One-based physical source line."),
    SchemaColumn("source_sha256", "VARCHAR", False, "SHA-256 of the source JSONL file."),
    SchemaColumn("timestamp_raw", "VARCHAR", False, "Unchanged supplied timestamp text."),
    SchemaColumn("timestamp_utc", "TIMESTAMPTZ", False, "Derived aware UTC instant.", "ISO 8601"),
    SchemaColumn("event_date_utc", "DATE", False, "UTC calendar date derived from timestamp_utc."),
    SchemaColumn("timestamp_offset_raw", "VARCHAR", False, "Original Z or numeric UTC offset."),
    SchemaColumn("service", "VARCHAR", False, "Supplied service value."),
    SchemaColumn("level", "VARCHAR", False, "Validated INFO, WARN, or ERROR level."),
    SchemaColumn("message_raw", "VARCHAR", False, "Unchanged supplied log message."),
    SchemaColumn("request_id", "VARCHAR", False, "Supplied request identifier."),
    SchemaColumn("trace_id", "VARCHAR", True, "Optional supplied trace identifier."),
    SchemaColumn("error_type", "VARCHAR", True, "Stable ERROR-only primary taxonomy."),
    SchemaColumn("error_code", "VARCHAR", True, "Explicit ERROR secondary code when present."),
    SchemaColumn(
        "related_component", "VARCHAR", True, "Explicit ERROR secondary component when present."
    ),
    SchemaColumn("path", "VARCHAR", True, "Explicit ERROR secondary path when present."),
    SchemaColumn(
        "error_parameters_json", "VARCHAR", False, "Sorted JSON of explicit ERROR parameters."
    ),
)


def _canonical_json(value: Any) -> bytes:
    serialized = json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )
    return (serialized + "\n").encode("utf-8")


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary.write(content)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def write_json_atomic(path: Path, value: Any) -> None:
    """Write canonical JSON through a same-directory atomic replacement."""
    _atomic_write_bytes(path, _canonical_json(value))


def write_jsonl_atomic(path: Path, values: Iterable[Any]) -> None:
    """Write ordered JSONL with stable per-record key ordering."""
    _atomic_write_bytes(path, b"".join(_canonical_json(value) for value in values))


def write_csv_atomic(path: Path, headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    """Write deterministic RFC-style CSV through an atomic replacement."""
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    _atomic_write_bytes(path, stream.getvalue().encode("utf-8"))


def _schema_document() -> dict[str, Any]:
    return {
        "columns": [
            {
                "name": column.name,
                "duckdb_type": column.duckdb_type,
                "nullable": column.nullable,
                "description": column.description,
                "format": column.format,
            }
            for column in CLEAN_RECORD_SCHEMA
        ],
        "parquet_rationale": "Typed Parquet keeps analytical scans reproducible while the ledger retains raw provenance.",
        "row_order": "source_line ascending",
    }


def write_schema(path: Path) -> None:
    """Publish the fixed schema and its reviewer-facing rationale."""
    write_json_atomic(path, _schema_document())


def _duckdb_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def write_parquet_atomic(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Write fixed-schema records ordered by physical source line through DuckDB."""
    ordered_records = sorted(records, key=lambda record: record["source_line"])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{next(tempfile._get_candidate_names())}.tmp")
    column_names = [column.name for column in CLEAN_RECORD_SCHEMA]
    definitions = ", ".join(f"{column.name} {column.duckdb_type}" for column in CLEAN_RECORD_SCHEMA)
    column_values = [
        [_duckdb_value(record.get(column)) for record in ordered_records] for column in column_names
    ]
    try:
        with duckdb.connect() as connection:
            connection.execute(f"CREATE TABLE clean_records ({definitions})")
            if ordered_records:
                projections = ", ".join(f"unnest(?) AS {column}" for column in column_names)
                connection.execute(
                    f"INSERT INTO clean_records ({', '.join(column_names)}) SELECT {projections}",
                    column_values,
                )
            escaped_path = str(temporary_path).replace("'", "''")
            connection.execute(
                "COPY (SELECT * FROM clean_records ORDER BY source_line) "
                f"TO '{escaped_path}' (FORMAT PARQUET, COMPRESSION zstd)"
            )
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
