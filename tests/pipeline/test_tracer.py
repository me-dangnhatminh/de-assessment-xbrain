from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import duckdb

from pipeline.__main__ import main

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPOSITORY_ROOT / "docs/onboard/datapack/data/app_logs_7days.jsonl"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_trace(output_root: Path, source_line: int = 1) -> None:
    result = main(
        [
            "trace",
            "--input",
            str(SOURCE),
            "--source-line",
            str(source_line),
            "--output-root",
            str(output_root),
        ]
    )
    assert result == 0


def test_trace_preserves_source_provenance_and_normalizes_real_error(tmp_path: Path) -> None:
    before_hash = sha256_file(SOURCE)
    output_root = tmp_path / "trace"

    run_trace(output_root)

    manifest = json.loads((output_root / "trace_manifest.json").read_text())
    ledger = json.loads((output_root / "quality_ledger.jsonl").read_text())
    parquet_record = duckdb.execute(
        "SELECT source_line, timestamp_raw, "
        "strftime(timezone('UTC', timestamp_utc), '%Y-%m-%dT%H:%M:%S') AS timestamp_utc, "
        "event_date_utc, message_raw, error_type, error_parameters_json FROM read_parquet(?)",
        [str(output_root / "trace.parquet")],
    ).fetchone()

    assert before_hash == sha256_file(SOURCE)
    assert manifest["source"]["line"] == 1
    assert manifest["source"]["sha256_before"] == before_hash
    assert manifest["source"]["sha256_after"] == before_hash
    assert ledger["source_line"] == 1
    assert ledger["final_action"] == "ACCEPT"
    assert ledger["retained_source_line"] == 1
    assert parquet_record == (
        1,
        "2026-07-27T00:02:47Z",
        "2026-07-27T00:02:47",
        date(2026, 7, 27),
        "ERR SMTPConnRefused host=mail-gw",
        "SMTP_CONN_REFUSED",
        '{"host":"mail-gw"}',
    )


def test_trace_emits_exactly_the_full_pipeline_row_for_the_same_source_line(
    tmp_path: Path,
) -> None:
    """Trace reuses the production stream, so its rows are byte-for-byte parity."""
    pipeline_root = tmp_path / "pipeline"
    trace_root = tmp_path / "trace"
    assert main(["run", "--input", str(SOURCE), "--output-root", str(pipeline_root)]) == 0
    run_trace(trace_root, source_line=1)

    full_ledger = json.loads(
        (pipeline_root / "evidence/phase1/quality_ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    trace_ledger = json.loads((trace_root / "quality_ledger.jsonl").read_text(encoding="utf-8"))
    assert trace_ledger == full_ledger

    columns = (
        "source_line, source_sha256, timestamp_raw, "
        "strftime(timezone('UTC', timestamp_utc), '%Y-%m-%dT%H:%M:%S') AS timestamp_utc, "
        "event_date_utc, timestamp_offset_raw, service, level, message_raw, request_id, trace_id, "
        "error_type, error_code, related_component, path, error_parameters_json"
    )
    full_row = duckdb.execute(
        f"SELECT {columns} FROM read_parquet(?) WHERE source_line = 1",
        [str(pipeline_root / "processed/logs_clean.parquet")],
    ).fetchone()
    trace_row = duckdb.execute(
        f"SELECT {columns} FROM read_parquet(?) WHERE source_line = 1",
        [str(trace_root / "trace.parquet")],
    ).fetchone()
    assert trace_row == full_row


def test_trace_writes_content_linked_ledger_parquet_sql_and_manifest(tmp_path: Path) -> None:
    output_root = tmp_path / "trace"
    run_trace(output_root)

    manifest = json.loads((output_root / "trace_manifest.json").read_text())
    artifacts = manifest["artifacts"]

    assert set(artifacts) == {
        "ledger",
        "parquet",
        "service_error_counts",
    }
    for artifact in artifacts.values():
        artifact_path = output_root / artifact["path"]
        assert artifact_path.is_file()
        assert artifact["sha256"] == sha256_file(artifact_path)
        assert artifact["row_count"] == 1

    assert manifest["analysis"]["sql_path"] == "pipeline/sql/00_tracer_service_error_counts.sql"
    assert manifest["analysis"]["sql_sha256"] == sha256_file(
        REPOSITORY_ROOT / manifest["analysis"]["sql_path"]
    )
    assert (output_root / "tables/00_tracer_service_error_counts.csv").read_text() == (
        "rank,service,error_count\n1,notification-worker,1\n"
    )


def test_trace_is_stable_across_fresh_output_roots(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"

    run_trace(first_root)
    run_trace(second_root)

    paths = [
        "quality_ledger.jsonl",
        "trace.parquet",
        "tables/00_tracer_service_error_counts.csv",
        "trace_manifest.json",
    ]
    assert {path: sha256_file(first_root / path) for path in paths} == {
        path: sha256_file(second_root / path) for path in paths
    }


def test_trace_rejects_output_inside_immutable_source_tree(tmp_path: Path) -> None:
    forbidden_root = REPOSITORY_ROOT / "docs/onboard/generated-trace"

    result = main(
        [
            "trace",
            "--input",
            str(SOURCE),
            "--source-line",
            "1",
            "--output-root",
            str(forbidden_root),
        ]
    )

    assert result != 0
    assert not forbidden_root.exists()


def test_trace_rejects_invalid_or_out_of_range_source_lines(tmp_path: Path) -> None:
    assert main(["trace", "--source-line", "0", "--output-root", str(tmp_path / "zero")]) != 0
    assert (
        main(["trace", "--source-line", "999999", "--output-root", str(tmp_path / "missing")]) != 0
    )
