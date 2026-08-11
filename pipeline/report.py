"""Evidence-only renderer for the Phase 1 reviewer-facing Markdown report."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pipeline.integrity import authorize_output_path
from pipeline.manifest import MANIFEST_PATH, ManifestVerificationError


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestVerificationError(f"cannot read report evidence: {path}") from error
    if not isinstance(value, dict):
        raise ManifestVerificationError(f"report evidence must be an object: {path}")
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ManifestVerificationError(f"report table is missing: {path}")
    with path.open(encoding="utf-8", newline="") as table:
        return list(csv.DictReader(table))


def _analysis_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {analysis["analysis_id"]: analysis for analysis in manifest["analyses"]}


def _evidence_chain(analysis: dict[str, Any]) -> list[str]:
    counts = ", ".join(f"{name}={value}" for name, value in analysis["relevant_row_counts"].items())
    return [
        f"- Manifest analysis ID: `{analysis['analysis_id']}`",
        f"- SQL: `{analysis['sql_path']}`",
        f"- Result table: `{analysis['result_path']}` ({analysis['result_row_count']} rows)",
        f"- Cleaned dataset SHA-256: `{analysis['cleaned_dataset_sha256']}`",
        f"- Relevant row counts: {counts}",
    ]


def render_report(output_root: Path) -> Path:
    """Render a report from generated tables and metadata, never by querying Parquet."""
    resolved_root = output_root.expanduser().resolve()
    evidence_root = resolved_root / "evidence/phase1"
    manifest = _read_json(resolved_root / MANIFEST_PATH)
    _read_json(evidence_root / "source_manifest.json")
    schema = _read_json(evidence_root / "schema.json")
    analyses = _analysis_by_id(manifest)
    service_rows = _read_csv(evidence_root / "tables/01_service_error_counts.csv")
    daily_rows = _read_csv(evidence_root / "tables/02_daily_error_counts.csv")
    error_rows = _read_csv(evidence_root / "tables/03_top_normalized_errors.csv")
    quality_rows = _read_csv(evidence_root / "tables/04_quality_reconciliation.csv")
    if not service_rows or not daily_rows or not error_rows or not quality_rows:
        raise ManifestVerificationError("report tables must contain generated evidence rows")

    highest_service = service_rows[0]
    unusual_day = next(row for row in daily_rows if row["is_unusual_by_2x_median_rule"] == "True")
    action_rows = {
        row["final_action"]: row for row in quality_rows if row["metric_type"] == "record_total"
    }
    unclassified = error_rows[0]["unclassified_error_count"]
    report_lines = [
        "# Phase 1: Auditable Log Pipeline Review",
        "",
        "This report renders the generated CSV tables and linked manifest metadata only; it does not query Parquet or recalculate customer aggregates.",
        "",
        "## Method and format",
        "",
        f"The cleaned dataset uses typed Parquet because {schema['parquet_rationale']}",
        "Every physical input line is retained in the quality ledger; only ACCEPT and REPAIR records are analytical rows.",
        "",
        "## Source integrity and quality totals",
        "",
        f"- Input lines: {action_rows['ACCEPT']['record_count']} accepted, {action_rows['REPAIR']['record_count']} repaired, and {action_rows['REJECT']['record_count']} rejected.",
        "- The quality reconciliation table proves input-to-action and analytical-to-Parquet conservation.",
        f"- UNCLASSIFIED_ERROR warning: {unclassified}. Raw ERROR messages are retained while unmatched signatures remain a normalization-quality warning.",
        "",
        "## 1. Service with the most ERROR records",
        "",
        f"**{highest_service['service']} ({highest_service['error_count']} ERROR records)** is highest in the seven-day cleaned dataset.",
        *_evidence_chain(analyses["service-error-counts"]),
        "",
        "## 2. Daily ERROR counts and unusual-day rule",
        "",
        f"**{unusual_day['event_date_utc']}** has {unusual_day['daily_error_count']} ERROR records, a ratio of {unusual_day['error_count_to_median_ratio']} to the seven-day median of {unusual_day['median_error_count']}.",
        "It is flagged only because the count exceeds twice the median; this is a descriptive seven-day heuristic, not a statistical anomaly detector.",
        f"Service contributions are {unusual_day['service_contributions']}; this contribution breakdown does not establish causation.",
        *_evidence_chain(analyses["daily-error-counts"]),
        "",
        "## 3. Top normalized ERROR types and services",
        "",
        *[
            f"- {row['rank']}. {row['error_type']}: {row['error_count']} ({row['service_contributions_json']})"
            for row in error_rows
        ],
        *_evidence_chain(analyses["top-normalized-errors"]),
        "",
        "## 4. Cleaning dispositions and issue types",
        "",
        *[
            f"- {row['issue_code']}: {row['record_count']} affected records ({row['issue_occurrences']} issue occurrences)"
            for row in quality_rows
            if row["metric_type"] == "issue_occurrence"
        ],
        *_evidence_chain(analyses["quality-reconciliation"]),
        "",
        "## Limitations and scope",
        "",
        "The unusual-day rule is descriptive only, and service contributions are evidence of distribution rather than root cause. This Phase 1 artifact does not make causal or statistical claims, deploy AWS infrastructure, or provide knowledge-base answers.",
    ]
    report_path = authorize_output_path(resolved_root, evidence_root / "report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=report_path.parent, delete=False, encoding="utf-8", mode="w"
    ) as temporary:
        temporary.write("\n".join(report_lines) + "\n")
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, report_path)
    return report_path
