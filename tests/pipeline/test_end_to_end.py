"""End-to-end contracts for the canonical Phase 1 reviewer workflow."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from pipeline.__main__ import build_parser, clean_generated_outputs, main
from pipeline.integrity import SourceIntegrityError, inventory_supplied_inputs

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPOSITORY_ROOT / "docs/onboard/datapack/data/app_logs_7days.jsonl"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_all_regenerates_deterministic_evidence_without_mutating_inputs(tmp_path: Path) -> None:
    """The canonical command runs every phase in D-14 order and regenerates stable evidence."""
    output_root = tmp_path / "generated"
    before = inventory_supplied_inputs()

    assert main(["all", "--input", str(SOURCE), "--output-root", str(output_root)]) == 0
    first_hashes = {
        relative: _sha256(output_root / relative)
        for relative in (
            "processed/logs_clean.parquet",
            "evidence/phase1/quality_ledger.jsonl",
            "evidence/phase1/schema.json",
            "evidence/phase1/source_manifest.json",
            "evidence/phase1/run_manifest.json",
            "evidence/phase1/report.md",
            "evidence/phase1/tables/01_service_error_counts.csv",
            "evidence/phase1/tables/02_daily_error_counts.csv",
            "evidence/phase1/tables/03_top_normalized_errors.csv",
            "evidence/phase1/tables/04_quality_reconciliation.csv",
        )
    }
    assert main(["all", "--clean", "--input", str(SOURCE), "--output-root", str(output_root)]) == 0
    assert {relative: _sha256(output_root / relative) for relative in first_hashes} == first_hashes
    assert inventory_supplied_inputs() == before


def test_all_cli_keeps_independent_stage_contracts() -> None:
    """Every stage accepts the same reviewer paths and maximum-line safety contract."""
    parser = build_parser()
    subcommands = next(action for action in parser._actions if action.dest == "subcommand")

    for command in ("integrity", "validate", "run", "analyze", "report", "verify", "all"):
        stage = subcommands.choices[command]
        options = {action.dest for action in stage._actions}
        assert {"input", "output_root", "max_line_bytes"} <= options


def test_clean_generated_outputs_is_limited_to_known_paths(tmp_path: Path) -> None:
    """Cleanup never permits a supplied tree or repository root as its target."""
    output_root = tmp_path / "generated"
    output_root.mkdir()
    (output_root / "unrelated.txt").write_text("keep", encoding="utf-8")
    (output_root / "processed").mkdir()
    (output_root / "processed/logs_clean.parquet").write_text("generated", encoding="utf-8")

    clean_generated_outputs(output_root)

    assert not (output_root / "processed/logs_clean.parquet").exists()
    assert (output_root / "unrelated.txt").read_text(encoding="utf-8") == "keep"
    with pytest.raises(SourceIntegrityError):
        clean_generated_outputs(REPOSITORY_ROOT)
    with pytest.raises(SourceIntegrityError):
        clean_generated_outputs(REPOSITORY_ROOT / "docs/onboard")


def test_makefile_and_readme_publish_the_locked_reviewer_path() -> None:
    """The canonical command and honest Phase 1 operating boundaries are documented."""
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

    for target in ("sync:", "integrity:", "pipeline:", "analysis:", "report:", "verify-phase1:", "phase1:"):
        assert target in makefile
    assert "uv run --locked python -m pipeline" in makefile
    assert "make phase1" in readme
    assert "docs/onboard/datapack/data/app_logs_7days.jsonl" in readme
    assert "Parquet" in readme
    assert "descriptive seven-day heuristic" in readme
    assert "AWS deployment" in readme
