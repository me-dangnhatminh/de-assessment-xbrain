"""Stage-oriented CLI for the auditable local log-pipeline proof of concept."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path

import duckdb

from pipeline.analysis import ANALYSIS_SPECS, AnalysisError, run_all_analyses, run_analysis
from pipeline.integrity import (
    CANONICAL_LOG_INPUT,
    SourceIntegrityError,
    assert_source_unchanged,
    authorize_output_path,
    inventory_supplied_inputs,
    require_canonical_log_input,
)
from pipeline.integrity import (
    sha256_file as integrity_sha256_file,
)
from pipeline.integrity import (
    validate_output_root as validate_generated_output_root,
)
from pipeline.manifest import ManifestVerificationError, build_run_manifest, verify_run_manifest
from pipeline.models import Disposition
from pipeline.reconstruct import reconstruct_evidence
from pipeline.report import render_report
from pipeline.write_outputs import (
    write_json_atomic,
    write_jsonl_atomic,
    write_schema,
)
from pipeline.write_outputs import (
    write_parquet_atomic as write_many_parquet_atomic,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = CANONICAL_LOG_INPUT
SQL_PATH = REPOSITORY_ROOT / "pipeline/sql/00_tracer_service_error_counts.sql"
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


def generated_path(output_root: Path, relative: Path | str) -> Path:
    """Resolve and authorize one generated artifact before it is written or unlinked."""
    return authorize_output_path(output_root, output_root / relative)


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
    """Trace one real immutable source line through the production evidence path.

    The traced row flows through the same reconstruct_evidence stream that run
    and verification use, so its ledger entry and Parquet row are exactly the
    production rows for that source line.
    """
    input_path = Path(arguments.input).expanduser().resolve()
    output_root = validate_output_root(Path(arguments.output_root))
    source_line = arguments.source_line
    if source_line < 1:
        raise TraceError("source line must be a positive integer")
    source_sha256_before = sha256_file(input_path)
    try:
        ledger_entries, clean_records = reconstruct_evidence(input_path, arguments.max_line_bytes)
    except (FileNotFoundError, ValueError) as error:
        raise TraceError(str(error)) from error
    ledger_row = next((entry for entry in ledger_entries if entry.source_line == source_line), None)
    if ledger_row is None:
        raise TraceError(f"source line {source_line} is outside the input file")
    if ledger_row.final_action not in {Disposition.ACCEPT, Disposition.REPAIR}:
        raise TraceError(f"source line {source_line} is rejected and cannot be traced analytically")
    clean_record = next(
        (record for record in clean_records if record["source_line"] == source_line), None
    )
    ledger_path = generated_path(output_root, "quality_ledger.jsonl")
    parquet_path = generated_path(output_root, "trace.parquet")
    result_path = generated_path(output_root, "tables/00_tracer_service_error_counts.csv")
    write_jsonl_atomic(ledger_path, (ledger_row.as_dict(),))
    write_many_parquet_atomic(parquet_path, [clean_record])
    result_row_count = write_service_counts(parquet_path, result_path)
    source_sha256_after = sha256_file(input_path)
    if source_sha256_after != source_sha256_before:
        raise TraceError("input source changed during trace execution")
    manifest = {
        "command": {
            "max_line_bytes": arguments.max_line_bytes,
            "source_line": source_line,
            "subcommand": "trace",
        },
        "source": {
            "line": source_line,
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
    write_json_atomic(generated_path(output_root, "trace_manifest.json"), manifest)
    return 0


def cmd_validate(arguments: argparse.Namespace) -> int:
    """Stream every input line into deterministic validation-ledger evidence."""
    input_path = Path(arguments.input).expanduser().resolve()
    output_root = validate_output_root(Path(arguments.output_root))
    source_sha256_before = sha256_file(input_path)
    try:
        ledger_entries, _ = reconstruct_evidence(input_path, arguments.max_line_bytes)
    except (FileNotFoundError, ValueError) as error:
        raise TraceError(str(error)) from error

    source_sha256_after = sha256_file(input_path)
    if source_sha256_after != source_sha256_before:
        raise TraceError("input source changed during validation")
    write_jsonl_atomic(
        generated_path(output_root, "quality_ledger.jsonl"),
        (entry.as_dict() for entry in ledger_entries),
    )
    return 0


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
        authorize_output_path(resolved_root, target)
        if target.is_file() or target.is_symlink():
            target.unlink()
    for directory in (
        resolved_root / "evidence/phase1/tables",
        resolved_root / "evidence/phase1",
        resolved_root / "evidence",
        resolved_root / "processed",
    ):
        authorize_output_path(resolved_root, directory)
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()


def cmd_run(arguments: argparse.Namespace) -> int:
    """Publish reconciled ledger, schema, manifest, and typed Parquet from immutable input."""
    input_path = require_canonical_log_input(Path(arguments.input))
    output_root = validate_output_root(Path(arguments.output_root))
    inventory_before = inventory_supplied_inputs()
    try:
        ledger_entries, clean_records = reconstruct_evidence(input_path, arguments.max_line_bytes)
    except (FileNotFoundError, ValueError) as error:
        raise TraceError(str(error)) from error

    final_actions = {action: 0 for action in Disposition}
    for entry in ledger_entries:
        final_actions[entry.final_action] += 1
    input_count = len(ledger_entries)
    analytical_count = final_actions[Disposition.ACCEPT] + final_actions[Disposition.REPAIR]
    if input_count != sum(final_actions.values()) or analytical_count != len(clean_records):
        raise TraceError("row conservation failed before evidence publication")

    ledger_path = generated_path(output_root, "evidence/phase1/quality_ledger.jsonl")
    schema_path = generated_path(output_root, "evidence/phase1/schema.json")
    manifest_path = generated_path(output_root, "evidence/phase1/source_manifest.json")
    parquet_path = generated_path(output_root, "processed/logs_clean.parquet")
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
    require_canonical_log_input(Path(arguments.input))
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
