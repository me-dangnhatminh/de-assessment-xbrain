"""Behavioral contracts for static-SQL customer analysis evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb

from pipeline.__main__ import main
from pipeline.analysis import ANALYSIS_SPECS, run_analysis

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPOSITORY_ROOT / "docs/onboard/datapack/data/app_logs_7days.jsonl"
PARQUET = REPOSITORY_ROOT / "data/processed/logs_clean.parquet"


def sha256_file(path: Path) -> str:
    """Return a digest for deterministic evidence assertions."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_service_error_counts_uses_static_sql_and_returns_deterministic_answer(
    tmp_path: Path,
) -> None:
    """The first row is the stable answer and all service counts reconcile to Parquet."""
    output_root = tmp_path / "output"

    result_path = run_analysis(
        "service-error-counts", parquet_path=PARQUET, output_root=output_root
    )

    assert result_path == output_root / "evidence/phase1/tables/01_service_error_counts.csv"
    rows = result_path.read_text(encoding="utf-8").splitlines()
    assert rows[0] == "rank,service,error_count"
    assert rows[1] == "1,payment-api,139"
    counts = [int(row.rsplit(",", maxsplit=1)[1]) for row in rows[1:]]
    with duckdb.connect() as connection:
        error_count = connection.execute(
            "SELECT count(*) FROM read_parquet(?) WHERE level = 'ERROR'", [str(PARQUET)]
        ).fetchone()[0]
    assert sum(counts) == error_count


def test_service_error_counts_registry_declares_all_final_contracts() -> None:
    """Plan 05 can add remaining SQL without renaming evidence contracts."""
    assert set(ANALYSIS_SPECS) == {
        "service-error-counts",
        "daily-error-counts",
        "top-normalized-errors",
        "quality-reconciliation",
    }
    assert ANALYSIS_SPECS["service-error-counts"].sql_path == Path(
        "pipeline/sql/01_service_error_counts.sql"
    )
    assert ANALYSIS_SPECS["service-error-counts"].result_path == Path(
        "evidence/phase1/tables/01_service_error_counts.csv"
    )
    assert ANALYSIS_SPECS["service-error-counts"].parameter_names == ("parquet_path",)
    assert ANALYSIS_SPECS["service-error-counts"].expected_columns == (
        "rank",
        "service",
        "error_count",
    )
    assert [spec.sql_path.name for spec in ANALYSIS_SPECS.values()] == [
        "01_service_error_counts.sql",
        "02_daily_error_counts.sql",
        "03_top_normalized_errors.sql",
        "04_quality_reconciliation.sql",
    ]


def test_service_error_counts_output_is_byte_stable_and_cli_runs_selected_id(
    tmp_path: Path,
) -> None:
    """The selected-ID CLI uses the registered SQL path and stable CSV serialization."""
    output_root = tmp_path / "output"
    command = [
        "analyze",
        "--analysis-id",
        "service-error-counts",
        "--input",
        str(SOURCE),
        "--output-root",
        str(output_root),
    ]

    assert main(["run", "--input", str(SOURCE), "--output-root", str(output_root)]) == 0
    assert main(command) == 0
    result_path = output_root / "evidence/phase1/tables/01_service_error_counts.csv"
    first_hash = sha256_file(result_path)
    assert main(command) == 0
    assert sha256_file(result_path) == first_hash


def test_service_error_counts_binds_parquet_path_without_sql_interpolation() -> None:
    """SQL has a parameter marker, keeping caller-controlled paths out of query text."""
    sql_path = REPOSITORY_ROOT / ANALYSIS_SPECS["service-error-counts"].sql_path
    sql = sql_path.read_text(encoding="utf-8")

    assert "read_parquet(?)" in sql
    assert str(PARQUET) not in sql
