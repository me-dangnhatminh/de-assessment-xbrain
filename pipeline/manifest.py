"""Content-linked Phase 1 evidence-manifest construction and verification."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import duckdb

from pipeline.analysis import ANALYSIS_SPECS
from pipeline.integrity import inventory_supplied_inputs, sha256_file, validate_output_root
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
        row_counts = source_manifest["row_counts"]
        source_inventory = source_manifest["source_inventory"]
    except KeyError as error:
        raise ManifestVerificationError(f"source manifest lacks {error.args[0]}") from error
    if not isinstance(row_counts, dict) or not isinstance(source_inventory, list):
        raise ManifestVerificationError("source manifest has invalid row-count or inventory data")

    artifacts = [
        _artifact(parquet_path, output_root, row_count=int(row_counts["parquet"])),
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


def _verify_source_inventory(manifest: dict[str, Any], source_manifest: dict[str, Any]) -> None:
    """Require live supplied bytes to agree with both persisted inventory layers."""
    source_inventory = source_manifest.get("source_inventory")
    run_inventory = manifest.get("source_inventory")
    if not isinstance(source_inventory, list):
        raise ManifestVerificationError("source manifest source_inventory is invalid")
    if not isinstance(run_inventory, list):
        raise ManifestVerificationError("run manifest source_inventory is invalid")

    live_inventory = inventory_supplied_inputs()
    if source_inventory != live_inventory:
        raise ManifestVerificationError(
            "source manifest source_inventory disagrees with live supplied inventory"
        )
    if run_inventory != live_inventory:
        raise ManifestVerificationError(
            "run manifest source_inventory disagrees with live supplied inventory"
        )


def _verify_row_counts(
    manifest: dict[str, Any], source_manifest: dict[str, Any], output_root: Path
) -> None:
    if manifest.get("row_counts") != source_manifest.get("row_counts"):
        raise ManifestVerificationError(
            "row_counts.parquet or related source-manifest count mismatch"
        )
    ledger_path = output_root / "evidence/phase1/quality_ledger.jsonl"
    if manifest["row_counts"].get("input") != _line_count(ledger_path):
        raise ManifestVerificationError("row_counts.input does not match quality ledger")


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
        actual_rows = _line_count(path) if path.suffix == ".jsonl" else None
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
    _verify_source_inventory(manifest, source_manifest)
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
