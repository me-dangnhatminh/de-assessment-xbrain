"""Static-SQL analysis registry and deterministic customer-evidence writers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

from pipeline.integrity import SourceIntegrityError, validate_output_root
from pipeline.write_outputs import write_csv_atomic

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class AnalysisError(ValueError):
    """Raised when an analysis contract cannot safely produce evidence."""


@dataclass(frozen=True)
class AnalysisSpec:
    """One fixed SQL-to-result evidence contract."""

    analysis_id: str
    sql_path: Path
    result_path: Path
    parameter_names: tuple[str, ...]
    expected_columns: tuple[str, ...]


ANALYSIS_SPECS = {
    "service-error-counts": AnalysisSpec(
        analysis_id="service-error-counts",
        sql_path=Path("pipeline/sql/01_service_error_counts.sql"),
        result_path=Path("evidence/phase1/tables/01_service_error_counts.csv"),
        parameter_names=("parquet_path",),
        expected_columns=("rank", "service", "error_count"),
    ),
    "daily-error-counts": AnalysisSpec(
        analysis_id="daily-error-counts",
        sql_path=Path("pipeline/sql/02_daily_error_counts.sql"),
        result_path=Path("evidence/phase1/tables/02_daily_error_counts.csv"),
        parameter_names=("parquet_path",),
        expected_columns=(
            "event_date_utc",
            "daily_error_count",
            "median_error_count",
            "error_count_to_median_ratio",
            "is_unusual_by_2x_median_rule",
            "service_contributions",
        ),
    ),
    "top-normalized-errors": AnalysisSpec(
        analysis_id="top-normalized-errors",
        sql_path=Path("pipeline/sql/03_top_normalized_errors.sql"),
        result_path=Path("evidence/phase1/tables/03_top_normalized_errors.csv"),
        parameter_names=("parquet_path",),
        expected_columns=(
            "rank",
            "error_type",
            "error_count",
            "service_contributions_json",
            "unclassified_error_count",
        ),
    ),
    "quality-reconciliation": AnalysisSpec(
        analysis_id="quality-reconciliation",
        sql_path=Path("pipeline/sql/04_quality_reconciliation.sql"),
        result_path=Path("evidence/phase1/tables/04_quality_reconciliation.csv"),
        parameter_names=("ledger_path",),
        expected_columns=(
            "metric_type",
            "issue_code",
            "final_action",
            "record_count",
            "issue_occurrences",
            "is_reconciled",
        ),
    ),
}


def _get_spec(analysis_id: str) -> AnalysisSpec:
    try:
        return ANALYSIS_SPECS[analysis_id]
    except KeyError as error:
        raise AnalysisError(f"unknown analysis id: {analysis_id}") from error


def _implementation_path(spec: AnalysisSpec) -> Path:
    path = (REPOSITORY_ROOT / spec.sql_path).resolve()
    if not path.is_file():
        raise AnalysisError(
            f"analysis SQL is not implemented yet for {spec.analysis_id}: {spec.sql_path}"
        )
    return path


def run_analysis(analysis_id: str, *, parquet_path: Path, output_root: Path) -> Path:
    """Execute one registered static query with values bound outside its SQL text."""
    spec = _get_spec(analysis_id)
    sql_path = _implementation_path(spec)
    try:
        generated_root = validate_output_root(output_root)
    except SourceIntegrityError as error:
        raise AnalysisError(str(error)) from error

    parameter_values: dict[str, Path] = {
        "parquet_path": parquet_path.expanduser().resolve(),
        "ledger_path": generated_root / "evidence/phase1/quality_ledger.jsonl",
    }
    for parameter_name in spec.parameter_names:
        try:
            parameter_path = parameter_values[parameter_name]
        except KeyError as error:
            raise AnalysisError(
                f"analysis {analysis_id} needs unsupported parameter: {parameter_name}"
            ) from error
        if not parameter_path.is_file():
            raise AnalysisError(f"analysis input does not exist: {parameter_path}")

    sql = sql_path.read_text(encoding="utf-8")
    with duckdb.connect() as connection:
        result = connection.execute(
            sql, [str(parameter_values[name]) for name in spec.parameter_names]
        )
        actual_columns = tuple(column[0] for column in result.description)
        if actual_columns != spec.expected_columns:
            raise AnalysisError(
                f"analysis {analysis_id} returned {actual_columns}, expected {spec.expected_columns}"
            )
        rows = result.fetchall()

    result_path = generated_root / spec.result_path
    write_csv_atomic(result_path, spec.expected_columns, rows)
    return result_path


def run_all_analyses(*, parquet_path: Path, output_root: Path) -> list[Path]:
    """Run only registered analyses whose checked-in SQL exists today."""
    return [
        run_analysis(spec.analysis_id, parquet_path=parquet_path, output_root=output_root)
        for spec in ANALYSIS_SPECS.values()
        if (REPOSITORY_ROOT / spec.sql_path).is_file()
    ]
