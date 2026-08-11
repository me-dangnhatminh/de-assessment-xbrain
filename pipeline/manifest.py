"""Content-linked Phase 1 evidence-manifest construction and verification."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import duckdb

from pipeline.analysis import ANALYSIS_SPECS
from pipeline.integrity import (
    CANONICAL_LOG_INPUT,
    SUPPLIED_ROOT,
    inventory_supplied_inputs,
    sha256_file,
    validate_output_root,
)
from pipeline.models import Disposition
from pipeline.write_outputs import write_json_atomic

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("evidence/phase1/run_manifest.json")


class ManifestVerificationError(ValueError):
    """Raised when an evidence manifest no longer represents its linked files."""


def _relative_output_path(path: Path, output_root: Path) -> str:
    return path.relative_to(output_root).as_posix()


def _line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as evidence:
        return sum(1 for _ in evidence)


def _csv_row_count(path: Path) -> int:
    return max(_line_count(path) - 1, 0)


def _parquet_row_count(path: Path) -> int:
    """Count live analytical rows through DuckDB without trusting a persisted declaration."""
    try:
        with duckdb.connect() as connection:
            result = connection.execute(
                "SELECT COUNT(*) FROM read_parquet(?)", [str(path)]
            ).fetchone()
    except (duckdb.Error, OSError) as error:
        raise ManifestVerificationError(f"cannot count Parquet artifact: {path}") from error
    if result is None or not isinstance(result[0], int):
        raise ManifestVerificationError(f"cannot count Parquet artifact: {path}")
    return result[0]


def _ledger_action_counts(path: Path) -> dict[str, int]:
    """Derive final-action totals from strict, line-oriented ledger evidence."""
    counts = {action.value: 0 for action in Disposition}
    try:
        with path.open(encoding="utf-8") as ledger:
            for line_number, line in enumerate(ledger, start=1):
                if not line.strip():
                    raise ManifestVerificationError(
                        f"quality ledger contains a blank line at {line_number}"
                    )
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ManifestVerificationError(
                        f"quality ledger contains malformed JSON at line {line_number}"
                    ) from error
                if not isinstance(entry, dict):
                    raise ManifestVerificationError(
                        f"quality ledger entry is not an object at line {line_number}"
                    )
                action = entry.get("final_action")
                if action not in counts:
                    raise ManifestVerificationError(
                        f"quality ledger final_action is invalid at line {line_number}"
                    )
                counts[action] += 1
    except OSError as error:
        raise ManifestVerificationError(f"cannot read quality ledger: {path}") from error
    return counts


def _uv_version() -> str:
    """Record the installed command version without making a network call."""
    executable = shutil.which("uv")
    if executable is None:
        return "unavailable (not on PATH)"
    completed = subprocess.run(
        [executable, "--version"], check=False, capture_output=True, text=True
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable (command failed)"


def _artifact(path: Path, output_root: Path, *, row_count: int | None = None) -> dict[str, Any]:
    """Return one stable content descriptor for an output-root artifact."""
    descriptor: dict[str, Any] = {
        "path": _relative_output_path(path, output_root),
        "sha256": sha256_file(path),
    }
    if row_count is not None:
        descriptor["row_count"] = row_count
    return descriptor


def _source_artifact(path: Path) -> dict[str, Any]:
    """Return one stable content descriptor for a checked-in implementation artifact."""
    return {"path": path.relative_to(REPOSITORY_ROOT).as_posix(), "sha256": sha256_file(path)}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestVerificationError(f"cannot read JSON evidence: {path}") from error
    if not isinstance(value, dict):
        raise ManifestVerificationError(f"JSON evidence must be an object: {path}")
    return value


def _manifest_payload(output_root: Path) -> dict[str, Any]:
    """Build the manifest body from existing generated evidence without recomputation."""
    source_manifest_path = output_root / "evidence/phase1/source_manifest.json"
    ledger_path = output_root / "evidence/phase1/quality_ledger.jsonl"
    schema_path = output_root / "evidence/phase1/schema.json"
    parquet_path = output_root / "processed/logs_clean.parquet"
    required_paths = (source_manifest_path, ledger_path, schema_path, parquet_path)
    for path in required_paths:
        if not path.is_file():
            raise ManifestVerificationError(f"required evidence artifact is missing: {path}")

    source_manifest = _read_json(source_manifest_path)
    try:
        source_row_counts = source_manifest["row_counts"]
        source_inventory = source_manifest["source_inventory"]
    except KeyError as error:
        raise ManifestVerificationError(f"source manifest lacks {error.args[0]}") from error
    if not isinstance(source_row_counts, dict) or not isinstance(source_inventory, list):
        raise ManifestVerificationError("source manifest has invalid row-count or inventory data")
    parquet_row_count = _parquet_row_count(parquet_path)
    row_counts = {**source_row_counts, "parquet": parquet_row_count}

    artifacts = [
        _artifact(parquet_path, output_root, row_count=parquet_row_count),
        _artifact(ledger_path, output_root, row_count=_line_count(ledger_path)),
        _artifact(schema_path, output_root),
        _artifact(source_manifest_path, output_root),
    ]
    report_path = output_root / "evidence/phase1/report.md"
    if report_path.is_file():
        artifacts.append(_artifact(report_path, output_root))

    analyses: list[dict[str, Any]] = []
    dataset_hash = sha256_file(parquet_path)
    for spec in ANALYSIS_SPECS.values():
        sql_path = REPOSITORY_ROOT / spec.sql_path
        result_path = output_root / spec.result_path
        if not sql_path.is_file():
            raise ManifestVerificationError(f"analysis SQL is missing: {spec.sql_path}")
        if not result_path.is_file():
            raise ManifestVerificationError(f"analysis result is missing: {spec.result_path}")
        artifacts.append(_source_artifact(sql_path))
        analyses.append(
            {
                "analysis_id": spec.analysis_id,
                "sql_path": spec.sql_path.as_posix(),
                "sql_sha256": sha256_file(sql_path),
                "result_path": _relative_output_path(result_path, output_root),
                "result_sha256": sha256_file(result_path),
                "result_row_count": _csv_row_count(result_path),
                "cleaned_dataset_sha256": dataset_hash,
                "relevant_row_counts": dict(sorted(row_counts.items())),
            }
        )

    commands = {
        "all": "uv run --locked python -m pipeline all --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data",
        "analyze": "uv run --locked python -m pipeline analyze --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data",
        "integrity": "uv run --locked python -m pipeline integrity --input docs/onboard/datapack/data/app_logs_7days.jsonl",
        "report": "uv run --locked python -m pipeline report --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data",
        "run": "uv run --locked python -m pipeline run --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data",
        "validate": "uv run --locked python -m pipeline validate --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data",
        "verify": "uv run --locked python -m pipeline verify --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data",
    }
    payload = {
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "source_inventory": source_inventory,
        "runtime": {
            "duckdb": duckdb.__version__,
            "python": sys.version.split()[0],
            "uv": _uv_version(),
        },
        "commands": commands,
        "row_counts": dict(sorted(row_counts.items())),
        "artifacts": sorted(artifacts, key=lambda item: item["path"]),
        "analyses": analyses,
    }
    run_id = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return {"run_id": run_id, **payload}


def build_run_manifest(output_root: Path) -> dict[str, Any]:
    """Build and atomically publish the deterministic Phase 1 evidence graph."""
    resolved_root = validate_output_root(output_root)
    manifest = _manifest_payload(resolved_root)
    write_json_atomic(resolved_root / MANIFEST_PATH, manifest)
    return manifest


def _verify_source_inventory(
    manifest: dict[str, Any], source_manifest: dict[str, Any], live_inventory: list[dict[str, str]]
) -> None:
    """Require live supplied bytes to agree with both persisted inventory layers."""
    source_inventory = source_manifest.get("source_inventory")
    run_inventory = manifest.get("source_inventory")
    if not isinstance(source_inventory, list):
        raise ManifestVerificationError("source manifest source_inventory is invalid")
    if not isinstance(run_inventory, list):
        raise ManifestVerificationError("run manifest source_inventory is invalid")

    if source_inventory != live_inventory:
        raise ManifestVerificationError(
            "source manifest source_inventory disagrees with live supplied inventory"
        )
    if run_inventory != live_inventory:
        raise ManifestVerificationError(
            "run manifest source_inventory disagrees with live supplied inventory"
        )


def _verify_input_binding(
    source_manifest: dict[str, Any], live_inventory: list[dict[str, str]]
) -> None:
    """Authenticate the persisted production-input descriptor against live supplied bytes."""
    descriptor = source_manifest.get("input")
    if not isinstance(descriptor, dict):
        raise ManifestVerificationError("source manifest input descriptor is invalid")
    descriptor_path = descriptor.get("path")
    descriptor_sha256 = descriptor.get("sha256")
    if not isinstance(descriptor_path, str) or not isinstance(descriptor_sha256, str):
        raise ManifestVerificationError("source manifest input descriptor is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", descriptor_sha256):
        raise ManifestVerificationError("source manifest input hash mismatch")

    descriptor_relative = Path(descriptor_path)
    if descriptor_relative.is_absolute() or ".." in descriptor_relative.parts:
        raise ManifestVerificationError("source manifest input membership mismatch")
    canonical_input = CANONICAL_LOG_INPUT.resolve()
    resolved_descriptor = (REPOSITORY_ROOT / descriptor_relative).resolve()
    if resolved_descriptor != canonical_input:
        raise ManifestVerificationError("source manifest input membership mismatch")

    expected_repository_path = canonical_input.relative_to(REPOSITORY_ROOT).as_posix()
    expected_inventory_path = canonical_input.relative_to(SUPPLIED_ROOT).as_posix()
    if descriptor_relative.as_posix() != expected_repository_path:
        raise ManifestVerificationError("source manifest input membership mismatch")

    source_inventory = source_manifest.get("source_inventory")
    if not isinstance(source_inventory, list):
        raise ManifestVerificationError("source manifest input membership mismatch")
    source_entry = next(
        (
            entry
            for entry in source_inventory
            if isinstance(entry, dict) and entry.get("path") == expected_inventory_path
        ),
        None,
    )
    live_entry = next(
        (
            entry
            for entry in live_inventory
            if isinstance(entry, dict) and entry.get("path") == expected_inventory_path
        ),
        None,
    )
    if source_entry is None or live_entry is None:
        raise ManifestVerificationError("source manifest input membership mismatch")

    live_sha256 = sha256_file(canonical_input)
    if (
        source_entry.get("sha256") != descriptor_sha256
        or live_entry.get("sha256") != descriptor_sha256
        or live_sha256 != descriptor_sha256
    ):
        raise ManifestVerificationError("source manifest input hash mismatch")


def _verify_row_counts(
    manifest: dict[str, Any], source_manifest: dict[str, Any], output_root: Path
) -> None:
    ledger_path = output_root / "evidence/phase1/quality_ledger.jsonl"
    parquet_path = output_root / "processed/logs_clean.parquet"
    action_counts = _ledger_action_counts(ledger_path)
    ledger_rows = sum(action_counts.values())
    parquet_rows = _parquet_row_count(parquet_path)
    live_counts = {
        "input": ledger_rows,
        "accept": action_counts[Disposition.ACCEPT.value],
        "repair": action_counts[Disposition.REPAIR.value],
        "reject": action_counts[Disposition.REJECT.value],
        "parquet": parquet_rows,
    }

    for layer_name, persisted_counts in (
        ("source manifest", source_manifest.get("row_counts")),
        ("run manifest", manifest.get("row_counts")),
    ):
        if not isinstance(persisted_counts, dict):
            raise ManifestVerificationError(f"{layer_name} row_counts is invalid")
        for count_name, live_count in live_counts.items():
            if persisted_counts.get(count_name) != live_count:
                raise ManifestVerificationError(
                    f"{layer_name} row_counts.{count_name} does not match live evidence"
                )

    if ledger_rows != (
        action_counts[Disposition.ACCEPT.value]
        + action_counts[Disposition.REPAIR.value]
        + action_counts[Disposition.REJECT.value]
    ):
        raise ManifestVerificationError("quality ledger action conservation failed")
    if (
        parquet_rows
        != action_counts[Disposition.ACCEPT.value] + action_counts[Disposition.REPAIR.value]
    ):
        raise ManifestVerificationError(
            "row_counts.parquet does not match ledger analytical actions"
        )


def _verify_artifact(descriptor: dict[str, Any], output_root: Path) -> None:
    relative_path = descriptor.get("path")
    if not isinstance(relative_path, str):
        raise ManifestVerificationError("artifact path is invalid")
    path = (
        REPOSITORY_ROOT / relative_path
        if relative_path.startswith("pipeline/")
        else output_root / relative_path
    )
    if not path.is_file():
        raise ManifestVerificationError(f"artifact is missing: {relative_path}")
    if descriptor.get("sha256") != sha256_file(path):
        raise ManifestVerificationError(f"artifact hash mismatch: {relative_path}")
    if "row_count" in descriptor:
        actual_rows = (
            _line_count(path)
            if path.suffix == ".jsonl"
            else _parquet_row_count(path)
            if path.suffix == ".parquet"
            else None
        )
        if actual_rows is not None and descriptor["row_count"] != actual_rows:
            raise ManifestVerificationError(f"artifact row count mismatch: {relative_path}")


def _verify_analysis(analysis: dict[str, Any], output_root: Path, dataset_hash: str) -> None:
    analysis_id = analysis.get("analysis_id")
    sql_path = analysis.get("sql_path")
    result_path = analysis.get("result_path")
    if (
        not isinstance(analysis_id, str)
        or not isinstance(sql_path, str)
        or not isinstance(result_path, str)
    ):
        raise ManifestVerificationError("analysis link is invalid")
    checked_in_sql = REPOSITORY_ROOT / sql_path
    generated_result = output_root / result_path
    if not checked_in_sql.is_file():
        raise ManifestVerificationError(f"analysis SQL is missing: {sql_path}")
    if not generated_result.is_file():
        raise ManifestVerificationError(f"analysis result is missing: {result_path}")
    if analysis.get("sql_sha256") != sha256_file(checked_in_sql):
        raise ManifestVerificationError(f"analysis SQL hash mismatch: {sql_path}")
    if analysis.get("result_sha256") != sha256_file(generated_result):
        raise ManifestVerificationError(f"analysis result hash mismatch: {result_path}")
    if analysis.get("result_row_count") != _csv_row_count(generated_result):
        raise ManifestVerificationError(f"analysis result row count mismatch: {result_path}")
    if analysis.get("cleaned_dataset_sha256") != dataset_hash:
        raise ManifestVerificationError(f"analysis dataset hash mismatch: {analysis_id}")


def verify_run_manifest(output_root: Path) -> None:
    """Fail closed if any manifest-linked artifact, count, or SQL/result link is stale."""
    resolved_root = validate_output_root(output_root)
    manifest_path = resolved_root / MANIFEST_PATH
    if not manifest_path.is_file():
        raise ManifestVerificationError(f"run manifest is missing: {MANIFEST_PATH.as_posix()}")
    manifest = _read_json(manifest_path)
    source_manifest = _read_json(resolved_root / "evidence/phase1/source_manifest.json")
    live_inventory = inventory_supplied_inputs()
    _verify_source_inventory(manifest, source_manifest, live_inventory)
    _verify_input_binding(source_manifest, live_inventory)
    _verify_row_counts(manifest, source_manifest, resolved_root)
    for artifact in manifest.get("artifacts", []):
        if not isinstance(artifact, dict):
            raise ManifestVerificationError("artifact entry is invalid")
        _verify_artifact(artifact, resolved_root)
    parquet_path = resolved_root / "processed/logs_clean.parquet"
    for analysis in manifest.get("analyses", []):
        if not isinstance(analysis, dict):
            raise ManifestVerificationError("analysis entry is invalid")
        _verify_analysis(analysis, resolved_root, sha256_file(parquet_path))
    expected = _manifest_payload(resolved_root)
    if manifest.get("run_id") != expected["run_id"]:
        raise ManifestVerificationError("run_id does not match linked evidence")
