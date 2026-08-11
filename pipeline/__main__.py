"""Stage-oriented CLI for the auditable local log-pipeline proof of concept."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from pipeline.analysis import ANALYSIS_SPECS, AnalysisError, run_all_analyses, run_analysis
from pipeline.ingest import canonical_record_digest, iter_source_lines, parse_json_line
from pipeline.integrity import (
    SourceIntegrityError,
    assert_source_unchanged,
    inventory_supplied_inputs,
)
from pipeline.integrity import (
    sha256_file as integrity_sha256_file,
)
from pipeline.integrity import (
    validate_output_root as validate_generated_output_root,
)
from pipeline.manifest import ManifestVerificationError, build_run_manifest, verify_run_manifest
from pipeline.models import CleanRecord, Disposition, LedgerEntry, Normalization
from pipeline.normalize import normalize_error, normalize_timestamp
from pipeline.report import render_report
from pipeline.validation import choose_final_action, make_issue, validate_record
from pipeline.write_outputs import (
    write_json_atomic,
    write_jsonl_atomic,
    write_schema,
)
from pipeline.write_outputs import (
    write_parquet_atomic as write_many_parquet_atomic,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPOSITORY_ROOT / "docs/onboard/datapack/data/app_logs_7days.jsonl"
SQL_PATH = REPOSITORY_ROOT / "pipeline/sql/00_tracer_service_error_counts.sql"
REQUIRED_FIELDS = ("timestamp", "service", "level", "message", "request_id")
MAX_LINE_BYTES = 1_048_576
GENERATED_PHASE1_PATHS = (
    Path("processed/logs_clean.parquet"),
    Path("evidence/phase1/quality_ledger.jsonl"),
    Path("evidence/phase1/schema.json"),
    Path("evidence/phase1/source_manifest.json"),
    Path("evidence/phase1/run_manifest.json"),
    Path("evidence/phase1/report.md"),
    *(spec.result_path for spec in ANALYSIS_SPECS.values()),
)


class TraceError(ValueError):
    """An actionable validation error for a trace invocation."""


def sha256_file(path: Path) -> str:
    """Return a SHA-256 digest without changing the supplied input."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    """Serialize JSON deterministically for evidence artifacts and hashes."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def atomic_write_bytes(path: Path, content: bytes) -> None:
    """Atomically replace a generated file after its complete content is available."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def validate_output_root(output_root: Path) -> Path:
    """Reject generated output locations that would mutate supplied inputs."""
    try:
        return validate_generated_output_root(output_root)
    except SourceIntegrityError as error:
        raise TraceError(str(error)) from error


def select_source_line(
    input_path: Path, source_line: int, max_line_bytes: int
) -> tuple[bytes, str]:
    """Read one physical source line as bytes before any JSON parsing."""
    if source_line < 1:
        raise TraceError("source line must be a positive integer")
    if max_line_bytes < 1:
        raise TraceError("max line bytes must be a positive integer")
    try:
        with input_path.open("rb") as source:
            for line_number, raw_bytes in enumerate(source, start=1):
                if line_number != source_line:
                    continue
                if len(raw_bytes) > max_line_bytes:
                    raise TraceError(
                        f"source line {source_line} exceeds max-line-bytes ({max_line_bytes})"
                    )
                try:
                    return raw_bytes, raw_bytes.decode("utf-8").rstrip("\r\n")
                except UnicodeDecodeError as error:
                    raise TraceError(f"source line {source_line} is not valid UTF-8") from error
    except FileNotFoundError as error:
        raise TraceError(f"input file not found: {input_path}") from error
    raise TraceError(f"source line {source_line} is outside the input file")


def parse_and_normalize(
    raw_line: str, source_line: int, source_sha256: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate the tracer's required fields and derive its normalized clean record."""
    try:
        source_record = json.loads(raw_line)
    except json.JSONDecodeError as error:
        raise TraceError(f"source line {source_line} contains invalid JSON") from error
    if not isinstance(source_record, dict):
        raise TraceError(f"source line {source_line} must contain a JSON object")
    invalid_fields = [
        field
        for field in REQUIRED_FIELDS
        if not isinstance(source_record.get(field), str) or not source_record[field]
    ]
    if invalid_fields:
        raise TraceError(
            f"source line {source_line} has missing or invalid fields: {', '.join(invalid_fields)}"
        )
    timestamp_raw = source_record["timestamp"]
    try:
        parsed_timestamp = datetime.fromisoformat(timestamp_raw)
    except ValueError as error:
        raise TraceError(f"source line {source_line} has an invalid timestamp") from error
    if parsed_timestamp.tzinfo is None:
        raise TraceError(f"source line {source_line} timestamp must include an offset")
    timestamp_utc = parsed_timestamp.astimezone(UTC)
    level = source_record["level"]
    message_raw = source_record["message"]
    error_type: str | None = None
    error_parameters: dict[str, str] = {}
    if level == "ERROR":
        signature = re.fullmatch(r"ERR\s+([A-Za-z][A-Za-z0-9_]*)\s*(.*)", message_raw)
        if signature is None:
            error_type = "UNCLASSIFIED_ERROR"
        else:
            error_type = signature.group(1)
            for token in signature.group(2).split():
                if "=" in token:
                    key, value = token.split("=", 1)
                    if key and value:
                        error_parameters[key] = value
    record_digest = hashlib.sha256(raw_line.encode("utf-8")).hexdigest()
    clean_record = {
        "source_line": source_line,
        "source_sha256": source_sha256,
        "timestamp_raw": timestamp_raw,
        "timestamp_utc": timestamp_utc.isoformat(),
        "event_date_utc": timestamp_utc.date().isoformat(),
        "timestamp_offset_raw": "Z" if timestamp_raw.endswith("Z") else timestamp_raw[-6:],
        "service": source_record["service"],
        "level": level,
        "message_raw": message_raw,
        "request_id": source_record["request_id"],
        "trace_id": source_record.get("trace_id"),
        "error_type": error_type,
        "error_code": None,
        "related_component": None,
        "path": None,
        "error_parameters_json": canonical_json(error_parameters),
    }
    ledger_row = {
        "source_path": "",
        "source_sha256": source_sha256,
        "source_line": source_line,
        "record_digest": record_digest,
        "raw_line": raw_line,
        "issues": [],
        "normalizations": ["timestamp_to_utc", "error_signature"]
        if level == "ERROR"
        else ["timestamp_to_utc"],
        "final_action": "accept",
        "retained_source_line": source_line,
    }
    return ledger_row, clean_record


def write_parquet_atomic(path: Path, record: dict[str, Any]) -> None:
    """Write the fixed tracer schema through a dedicated DuckDB connection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    column_definitions = (
        "source_line BIGINT, source_sha256 VARCHAR, timestamp_raw VARCHAR, timestamp_utc VARCHAR, "
        "event_date_utc DATE, timestamp_offset_raw VARCHAR, service VARCHAR, level VARCHAR, "
        "message_raw VARCHAR, request_id VARCHAR, trace_id VARCHAR, error_type VARCHAR, "
        "error_code VARCHAR, related_component VARCHAR, path VARCHAR, error_parameters_json VARCHAR"
    )
    columns = list(record)
    with duckdb.connect() as connection:
        connection.execute(f"CREATE TABLE trace_record ({column_definitions})")
        connection.execute(
            f"INSERT INTO trace_record ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            [record[column] for column in columns],
        )
        escaped_path = str(temporary_path).replace("'", "''")
        connection.execute(
            f"COPY trace_record TO '{escaped_path}' (FORMAT PARQUET, COMPRESSION 'zstd')"
        )
    os.replace(temporary_path, path)


def write_service_counts(parquet_path: Path, output_path: Path) -> int:
    """Execute checked-in SQL with parameters and write deterministic CSV evidence."""
    with duckdb.connect() as connection:
        rows = connection.execute(
            SQL_PATH.read_text(encoding="utf-8"), [str(parquet_path), "ERROR"]
        ).fetchall()
    output = ["rank,service,error_count"]
    output.extend(",".join(str(value) for value in row) for row in rows)
    atomic_write_bytes(output_path, ("\n".join(output) + "\n").encode("utf-8"))
    return len(rows)


def cmd_trace(arguments: argparse.Namespace) -> int:
    """Trace one real immutable JSONL record through every Phase 1 evidence seam."""
    input_path = Path(arguments.input).expanduser().resolve()
    output_root = validate_output_root(Path(arguments.output_root))
    source_sha256_before = sha256_file(input_path)
    _, raw_line = select_source_line(input_path, arguments.source_line, arguments.max_line_bytes)
    ledger_row, clean_record = parse_and_normalize(
        raw_line, arguments.source_line, source_sha256_before
    )
    ledger_row["source_path"] = str(input_path)
    ledger_path = output_root / "quality_ledger.jsonl"
    parquet_path = output_root / "trace.parquet"
    result_path = output_root / "tables/00_tracer_service_error_counts.csv"
    atomic_write_bytes(ledger_path, (canonical_json(ledger_row) + "\n").encode("utf-8"))
    write_parquet_atomic(parquet_path, clean_record)
    result_row_count = write_service_counts(parquet_path, result_path)
    source_sha256_after = sha256_file(input_path)
    if source_sha256_after != source_sha256_before:
        raise TraceError("input source changed during trace execution")
    manifest = {
        "command": {
            "max_line_bytes": arguments.max_line_bytes,
            "source_line": arguments.source_line,
            "subcommand": "trace",
        },
        "source": {
            "line": arguments.source_line,
            "path": str(input_path),
            "sha256_after": source_sha256_after,
            "sha256_before": source_sha256_before,
        },
        "row_counts": {"ledger": 1, "parquet": 1, "service_error_counts": result_row_count},
        "artifacts": {
            "ledger": {
                "path": ledger_path.relative_to(output_root).as_posix(),
                "row_count": 1,
                "sha256": sha256_file(ledger_path),
            },
            "parquet": {
                "path": parquet_path.relative_to(output_root).as_posix(),
                "row_count": 1,
                "sha256": sha256_file(parquet_path),
            },
            "service_error_counts": {
                "path": result_path.relative_to(output_root).as_posix(),
                "row_count": result_row_count,
                "sha256": sha256_file(result_path),
            },
        },
        "analysis": {
            "sql_path": SQL_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
            "sql_sha256": sha256_file(SQL_PATH),
        },
    }
    atomic_write_bytes(
        output_root / "trace_manifest.json", (canonical_json(manifest) + "\n").encode("utf-8")
    )
    return 0


def cmd_validate(arguments: argparse.Namespace) -> int:
    """Stream every input line into deterministic validation-ledger evidence."""
    input_path = Path(arguments.input).expanduser().resolve()
    output_root = validate_output_root(Path(arguments.output_root))
    source_sha256_before = sha256_file(input_path)
    ledger_entries: list[LedgerEntry] = []
    first_source_line_by_digest: dict[str, int] = {}
    try:
        envelopes = iter_source_lines(input_path, arguments.max_line_bytes)
        for envelope in envelopes:
            record, issues = parse_json_line(envelope)
            if record is not None:
                issues = (*issues, *validate_record(record))
                record_digest = canonical_record_digest(record)
                retained_source_line = first_source_line_by_digest.setdefault(
                    record_digest, envelope.source_line
                )
                if retained_source_line != envelope.source_line:
                    issues = (
                        *issues,
                        make_issue(
                            "EXACT_DUPLICATE",
                            None,
                            record_digest,
                            retained_source_line,
                        ),
                    )
            else:
                record_digest = None
                retained_source_line = None
            ledger_entries.append(
                LedgerEntry(
                    source_path=envelope.source_path,
                    source_sha256=envelope.source_sha256,
                    source_line=envelope.source_line,
                    record_digest=record_digest,
                    raw_line=envelope.raw_line,
                    issues=issues,
                    normalizations=(),
                    final_action=choose_final_action(issues),
                    retained_source_line=retained_source_line,
                )
            )
    except (FileNotFoundError, ValueError) as error:
        raise TraceError(str(error)) from error

    source_sha256_after = sha256_file(input_path)
    if source_sha256_after != source_sha256_before:
        raise TraceError("input source changed during validation")
    ledger_content = "".join(canonical_json(entry.as_dict()) + "\n" for entry in ledger_entries)
    atomic_write_bytes(output_root / "quality_ledger.jsonl", ledger_content.encode("utf-8"))
    return 0


def _run_validation_stream(
    input_path: Path, max_line_bytes: int
) -> tuple[list[LedgerEntry], list[dict[str, Any]]]:
    """Validate every physical line and normalize only analytical final actions."""
    ledger_entries: list[LedgerEntry] = []
    clean_records: list[dict[str, Any]] = []
    first_source_line_by_digest: dict[str, int] = {}
    for envelope in iter_source_lines(input_path, max_line_bytes):
        record, issues = parse_json_line(envelope)
        if record is not None:
            issues = (*issues, *validate_record(record))
            record_digest = canonical_record_digest(record)
            retained_source_line = first_source_line_by_digest.setdefault(
                record_digest, envelope.source_line
            )
            if retained_source_line != envelope.source_line:
                issues = (
                    *issues,
                    make_issue("EXACT_DUPLICATE", None, record_digest, retained_source_line),
                )
        else:
            record_digest = None
            retained_source_line = None
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


def cmd_integrity(arguments: argparse.Namespace) -> int:
    """Report the complete supplied-file inventory without generating artifacts."""
    inventory = inventory_supplied_inputs()
    input_path = Path(arguments.input).expanduser().resolve()
    print(f"files={len(inventory)} sha256={integrity_sha256_file(input_path)}")
    return 0


def clean_generated_outputs(output_root: Path) -> None:
    """Remove only known Phase 1 artifacts from a validated generated-output root."""
    resolved_root = validate_generated_output_root(output_root)
    if resolved_root in {REPOSITORY_ROOT, REPOSITORY_ROOT / "docs/onboard"}:
        raise SourceIntegrityError("clean refuses the repository root and supplied source tree")
    for relative_path in GENERATED_PHASE1_PATHS:
        target = resolved_root / relative_path
        if target.is_file() or target.is_symlink():
            target.unlink()
    for directory in (
        resolved_root / "evidence/phase1/tables",
        resolved_root / "evidence/phase1",
        resolved_root / "evidence",
        resolved_root / "processed",
    ):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()


def cmd_run(arguments: argparse.Namespace) -> int:
    """Publish reconciled ledger, schema, manifest, and typed Parquet from immutable input."""
    input_path = Path(arguments.input).expanduser().resolve()
    output_root = validate_output_root(Path(arguments.output_root))
    inventory_before = inventory_supplied_inputs()
    try:
        ledger_entries, clean_records = _run_validation_stream(input_path, arguments.max_line_bytes)
    except (FileNotFoundError, ValueError) as error:
        raise TraceError(str(error)) from error

    final_actions = {action: 0 for action in Disposition}
    for entry in ledger_entries:
        final_actions[entry.final_action] += 1
    input_count = len(ledger_entries)
    analytical_count = final_actions[Disposition.ACCEPT] + final_actions[Disposition.REPAIR]
    if input_count != sum(final_actions.values()) or analytical_count != len(clean_records):
        raise TraceError("row conservation failed before evidence publication")

    ledger_path = output_root / "evidence/phase1/quality_ledger.jsonl"
    schema_path = output_root / "evidence/phase1/schema.json"
    manifest_path = output_root / "evidence/phase1/source_manifest.json"
    parquet_path = output_root / "processed/logs_clean.parquet"
    write_jsonl_atomic(ledger_path, (entry.as_dict() for entry in ledger_entries))
    write_schema(schema_path)
    write_many_parquet_atomic(parquet_path, clean_records)
    inventory_after = inventory_supplied_inputs()
    assert_source_unchanged(inventory_before, inventory_after)
    manifest = {
        "input": {
            "path": input_path.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": integrity_sha256_file(input_path),
        },
        "source_inventory": inventory_before,
        "row_counts": {
            "input": input_count,
            "accept": final_actions[Disposition.ACCEPT],
            "repair": final_actions[Disposition.REPAIR],
            "reject": final_actions[Disposition.REJECT],
            "parquet": len(clean_records),
        },
        "conservation": {
            "input_equals_actions": input_count == sum(final_actions.values()),
            "analytical_equals_parquet": analytical_count == len(clean_records),
        },
    }
    write_json_atomic(manifest_path, manifest)
    unclassified_errors = sum(
        record["error_type"] == "UNCLASSIFIED_ERROR" for record in clean_records
    )
    print(
        "final_actions "
        f"accept={final_actions[Disposition.ACCEPT]} "
        f"repair={final_actions[Disposition.REPAIR]} "
        f"reject={final_actions[Disposition.REJECT]} "
        f"unclassified_errors={unclassified_errors}"
    )
    return 0


def cmd_analyze(arguments: argparse.Namespace) -> int:
    """Generate registered customer-analysis tables from existing cleaned Parquet."""
    output_root = validate_output_root(Path(arguments.output_root))
    parquet_path = output_root / "processed/logs_clean.parquet"
    if getattr(arguments, "analysis_id", None) is None:
        generated_paths = run_all_analyses(parquet_path=parquet_path, output_root=output_root)
    else:
        generated_paths = [
            run_analysis(arguments.analysis_id, parquet_path=parquet_path, output_root=output_root)
        ]
    for generated_path in generated_paths:
        print(generated_path.relative_to(output_root).as_posix())
    return 0


def cmd_report(arguments: argparse.Namespace) -> int:
    """Publish the report and its final content-linked manifest entry."""
    output_root = validate_output_root(Path(arguments.output_root))
    build_run_manifest(output_root)
    report_path = render_report(output_root)
    build_run_manifest(output_root)
    print(report_path.relative_to(output_root).as_posix())
    return 0


def cmd_verify(arguments: argparse.Namespace) -> int:
    """Verify every manifest-linked Phase 1 artifact without regenerating it."""
    output_root = validate_output_root(Path(arguments.output_root))
    verify_run_manifest(output_root)
    print("run manifest verified")
    return 0


def cmd_all(arguments: argparse.Namespace) -> int:
    """Run D-14 stages in order with immutable-source checks before and after."""
    output_root = validate_output_root(Path(arguments.output_root))
    source_before = inventory_supplied_inputs()
    if arguments.clean:
        clean_generated_outputs(output_root)
    cmd_integrity(arguments)
    cmd_run(arguments)
    cmd_analyze(arguments)
    cmd_report(arguments)
    cmd_verify(arguments)
    assert_source_unchanged(source_before, inventory_supplied_inputs())
    return 0


def _add_stage_arguments(
    parser: argparse.ArgumentParser, *, clean: bool = False, output_required: bool = True
) -> None:
    """Keep independently runnable stages on one reviewer-facing argument contract."""
    parser.add_argument("--input", default=DEFAULT_INPUT, type=Path)
    parser.add_argument("--output-root", default=Path("data"), required=output_required, type=Path)
    parser.add_argument("--max-line-bytes", default=MAX_LINE_BYTES, type=int)
    if clean:
        parser.add_argument("--clean", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    """Build the durable stage-oriented command-line interface."""
    parser = argparse.ArgumentParser(prog="python -m pipeline")
    subcommands = parser.add_subparsers(dest="subcommand", required=True)
    trace_parser = subcommands.add_parser("trace", help="trace one immutable log line")
    trace_parser.add_argument("--input", default=DEFAULT_INPUT, type=Path)
    trace_parser.add_argument("--source-line", default=1, type=int)
    trace_parser.add_argument("--output-root", required=True, type=Path)
    trace_parser.add_argument("--max-line-bytes", default=MAX_LINE_BYTES, type=int)
    trace_parser.set_defaults(handler=cmd_trace)
    validate_parser = subcommands.add_parser("validate", help="validate every immutable log line")
    _add_stage_arguments(validate_parser)
    validate_parser.set_defaults(handler=cmd_validate)
    integrity_parser = subcommands.add_parser(
        "integrity", help="inventory immutable supplied files"
    )
    _add_stage_arguments(integrity_parser, output_required=False)
    integrity_parser.set_defaults(handler=cmd_integrity)
    run_parser = subcommands.add_parser("run", help="publish reconciled Phase 1 base evidence")
    _add_stage_arguments(run_parser)
    run_parser.set_defaults(handler=cmd_run)
    analyze_parser = subcommands.add_parser(
        "analyze", help="run registered static SQL over cleaned Parquet"
    )
    analyze_parser.add_argument("--analysis-id")
    _add_stage_arguments(analyze_parser)
    analyze_parser.set_defaults(handler=cmd_analyze)
    report_parser = subcommands.add_parser("report", help="render the linked reviewer report")
    _add_stage_arguments(report_parser)
    report_parser.set_defaults(handler=cmd_report)
    verify_parser = subcommands.add_parser("verify", help="verify linked Phase 1 evidence")
    _add_stage_arguments(verify_parser)
    verify_parser.set_defaults(handler=cmd_verify)
    all_parser = subcommands.add_parser("all", help="run every Phase 1 stage in D-14 order")
    _add_stage_arguments(all_parser, clean=True)
    all_parser.set_defaults(handler=cmd_all)
    return parser


def main(arguments: list[str] | None = None) -> int:
    """Run a pipeline subcommand and report actionable validation failures."""
    parser = build_parser()
    parsed_arguments = parser.parse_args(arguments)
    try:
        return parsed_arguments.handler(parsed_arguments)
    except (AnalysisError, ManifestVerificationError, TraceError, SourceIntegrityError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
