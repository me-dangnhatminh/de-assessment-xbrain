"""Behavioral contracts for static-SQL customer analysis evidence."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import duckdb
import pytest

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


def test_analysis_registry_rejects_an_explicit_unimplemented_query(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An explicit future ID fails instead of silently omitting evidence."""
    result = main(
        [
            "analyze",
            "--analysis-id",
            "top-normalized-errors",
            "--output-root",
            str(tmp_path / "output"),
        ]
    )

    assert result == 2
    assert "not implemented yet" in capsys.readouterr().err


def test_daily_error_counts_uses_seven_utc_dates_and_cleaned_error_rows(tmp_path: Path) -> None:
    """The daily table covers the locked UTC window, including zero-count dates if needed."""
    result_path = run_analysis(
        "daily-error-counts", parquet_path=PARQUET, output_root=tmp_path / "output"
    )

    rows = list(csv.DictReader(result_path.open(encoding="utf-8")))
    assert [row["event_date_utc"] for row in rows] == [
        "2026-07-27",
        "2026-07-28",
        "2026-07-29",
        "2026-07-30",
        "2026-07-31",
        "2026-08-01",
        "2026-08-02",
    ]
    assert [int(row["daily_error_count"]) for row in rows] == [19, 27, 29, 140, 17, 24, 31]
    assert all(row["median_error_count"] == "27.0" for row in rows)


def test_daily_error_counts_applies_only_the_strict_descriptive_median_rule(
    tmp_path: Path,
) -> None:
    """A count equal to twice median is not unusual; only the 140-count day is flagged."""
    result_path = run_analysis(
        "daily-error-counts", parquet_path=PARQUET, output_root=tmp_path / "output"
    )
    rows = list(csv.DictReader(result_path.open(encoding="utf-8")))

    assert [row["is_unusual_by_2x_median_rule"] for row in rows] == [
        "False",
        "False",
        "False",
        "True",
        "False",
        "False",
        "False",
    ]
    flagged = next(row for row in rows if row["is_unusual_by_2x_median_rule"] == "True")
    assert flagged["event_date_utc"] == "2026-07-30"
    assert float(flagged["error_count_to_median_ratio"]) == 140 / 27


def test_daily_error_counts_contributions_reconcile_without_a_causation_claim(
    tmp_path: Path,
) -> None:
    """Flagged-day detail is a deterministic service contribution, not an explanation."""
    result_path = run_analysis(
        "daily-error-counts", parquet_path=PARQUET, output_root=tmp_path / "output"
    )
    rows = list(csv.DictReader(result_path.open(encoding="utf-8")))
    flagged = next(row for row in rows if row["is_unusual_by_2x_median_rule"] == "True")
    contributions = [
        part.split(":", maxsplit=1) for part in flagged["service_contributions"].split(";")
    ]

    assert contributions == sorted(contributions)
    assert sum(int(count) for _, count in contributions) == int(flagged["daily_error_count"])
    assert "cause" not in result_path.read_text(encoding="utf-8").lower()


def test_daily_error_counts_groups_offset_boundary_records_by_event_date_utc(
    tmp_path: Path,
) -> None:
    """Source-text 2026-08-03 records remain in the official UTC daily window."""
    result_path = run_analysis(
        "daily-error-counts", parquet_path=PARQUET, output_root=tmp_path / "output"
    )
    with duckdb.connect() as connection:
        normalized_boundary_count = connection.execute(
            "SELECT count(*) FROM read_parquet(?) "
            "WHERE level = 'ERROR' AND timestamp_raw LIKE '2026-08-03%' "
            "AND event_date_utc = DATE '2026-08-02'",
            [str(PARQUET)],
        ).fetchone()[0]

    assert normalized_boundary_count > 0
    assert "2026-08-03" not in result_path.read_text(encoding="utf-8")
