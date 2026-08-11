"""Behavioral contracts for the Phase 1 manifest and reviewer report."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from pipeline.__main__ import main
from pipeline.manifest import ManifestVerificationError, build_run_manifest, verify_run_manifest
from pipeline.report import render_report

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPOSITORY_ROOT / "docs/onboard/datapack/data/app_logs_7days.jsonl"


def _build_evidence(output_root: Path) -> None:
    """Generate the existing pipeline and SQL evidence through public CLI stages."""
    assert main(["run", "--input", str(SOURCE), "--output-root", str(output_root)]) == 0
    assert main(["analyze", "--input", str(SOURCE), "--output-root", str(output_root)]) == 0


def test_manifest_is_deterministic_and_links_every_evidence_artifact(tmp_path: Path) -> None:
    """The graph binds source inventory, runtime, commands, hashes, counts, and analyses."""
    output_root = tmp_path / "output"
    _build_evidence(output_root)

    first = build_run_manifest(output_root)
    second = build_run_manifest(output_root)

    assert first == second
    assert first["run_id"]
    assert first["source_manifest_sha256"]
    assert set(first["runtime"]) == {"duckdb", "python", "uv"}
    assert {"all", "analyze", "integrity", "report", "run", "validate", "verify"} <= set(
        first["commands"]
    )
    assert first["row_counts"] == {
        "accept": 2839,
        "input": 2923,
        "parquet": 2839,
        "reject": 84,
        "repair": 0,
    }
    artifact_paths = {artifact["path"] for artifact in first["artifacts"]}
    assert {
        "processed/logs_clean.parquet",
        "evidence/phase1/quality_ledger.jsonl",
        "evidence/phase1/schema.json",
        "evidence/phase1/source_manifest.json",
    } <= artifact_paths
    assert {analysis["analysis_id"] for analysis in first["analyses"]} == {
        "service-error-counts",
        "daily-error-counts",
        "top-normalized-errors",
        "quality-reconciliation",
    }
    for analysis in first["analyses"]:
        assert {
            "analysis_id",
            "sql_path",
            "sql_sha256",
            "result_path",
            "result_sha256",
            "result_row_count",
            "cleaned_dataset_sha256",
            "relevant_row_counts",
        } <= set(analysis)


def test_manifest_verification_accepts_matching_live_source_inventory(tmp_path: Path) -> None:
    """Verification accepts evidence whose two saved inventories match live supplied bytes."""
    output_root = tmp_path / "output"
    _build_evidence(output_root)
    build_run_manifest(output_root)

    verify_run_manifest(output_root)


def test_manifest_verification_rejects_forged_source_inventory_after_rebuild(
    tmp_path: Path,
) -> None:
    """Rebuilt derived metadata cannot authenticate a forged source inventory."""
    output_root = tmp_path / "output"
    _build_evidence(output_root)
    build_run_manifest(output_root)

    source_manifest_path = output_root / "evidence/phase1/source_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_manifest["source_inventory"][0]["sha256"] = "0" * 64
    source_manifest_path.write_text(
        json.dumps(source_manifest, sort_keys=True), encoding="utf-8"
    )
    build_run_manifest(output_root)

    with pytest.raises(ManifestVerificationError, match="source manifest source_inventory"):
        verify_run_manifest(output_root)


def test_manifest_verification_requires_three_way_source_inventory_equality(
    tmp_path: Path,
) -> None:
    """Live bytes must match each persisted inventory, not only one saved layer."""
    output_root = tmp_path / "output"
    _build_evidence(output_root)
    build_run_manifest(output_root)

    source_manifest_path = output_root / "evidence/phase1/source_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_manifest["source_inventory"][0]["sha256"] = "0" * 64
    source_manifest_path.write_text(
        json.dumps(source_manifest, sort_keys=True), encoding="utf-8"
    )

    with pytest.raises(ManifestVerificationError, match="source manifest source_inventory"):
        verify_run_manifest(output_root)


def test_report_renders_only_generated_table_values_and_direct_evidence_links(
    tmp_path: Path,
) -> None:
    """Report prose is sourced from CSV evidence and keeps qualified seven-day language."""
    output_root = tmp_path / "output"
    _build_evidence(output_root)
    build_run_manifest(output_root)

    report_path = render_report(output_root)
    report = report_path.read_text(encoding="utf-8")
    service_rows = list(
        csv.DictReader(
            (output_root / "evidence/phase1/tables/01_service_error_counts.csv").open(
                encoding="utf-8"
            )
        )
    )

    assert report_path == output_root / "evidence/phase1/report.md"
    assert (
        f"{service_rows[0]['service']} ({service_rows[0]['error_count']} ERROR records)" in report
    )
    assert "5.185185185185185" in report
    assert "descriptive seven-day heuristic" in report
    assert "does not establish causation" in report
    assert "UNCLASSIFIED_ERROR warning: 35" in report
    assert report.count("Manifest analysis ID") == 4
    assert report.count("Cleaned dataset SHA-256") == 4
    assert "pipeline/sql/01_service_error_counts.sql" in report
    assert "evidence/phase1/tables/04_quality_reconciliation.csv" in report


@pytest.mark.parametrize(
    ("relative_path", "mutation"),
    [
        ("evidence/phase1/tables/01_service_error_counts.csv", "tampered result\n"),
        ("pipeline/sql/01_service_error_counts.sql", "-- tampered query\n"),
    ],
)
def test_manifest_verification_detects_tampered_artifacts_and_queries(
    tmp_path: Path, relative_path: str, mutation: str
) -> None:
    """Verification identifies the mismatched file rather than accepting stale evidence."""
    output_root = tmp_path / "output"
    _build_evidence(output_root)
    build_run_manifest(output_root)

    target = (
        REPOSITORY_ROOT / relative_path
        if relative_path.startswith("pipeline/")
        else output_root / relative_path
    )
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(original + mutation, encoding="utf-8")
        with pytest.raises(ManifestVerificationError, match=relative_path):
            verify_run_manifest(output_root)
    finally:
        if relative_path.startswith("pipeline/"):
            target.write_text(original, encoding="utf-8")


def test_manifest_verification_detects_tampered_count_and_analysis_link(tmp_path: Path) -> None:
    """Semantic graph checks cover stale declared counts and broken query/result references."""
    output_root = tmp_path / "output"
    _build_evidence(output_root)
    manifest = build_run_manifest(output_root)
    manifest_path = output_root / "evidence/phase1/run_manifest.json"

    manifest["row_counts"]["parquet"] += 1
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    with pytest.raises(ManifestVerificationError, match="row_counts.parquet"):
        verify_run_manifest(output_root)

    manifest = build_run_manifest(output_root)
    manifest["analyses"][0]["result_path"] = "evidence/phase1/tables/missing.csv"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    with pytest.raises(ManifestVerificationError, match="missing.csv"):
        verify_run_manifest(output_root)
