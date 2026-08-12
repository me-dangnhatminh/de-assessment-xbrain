"""Generate the consolidated root run_manifest.json aggregating all phase evidence.

Deterministic: content-derived run_id, no wall-clock fields, sorted keys.
Mirrors the pattern from pipeline/manifest.py but scopes to the full submission.

Usage:
    python scripts/make_manifest.py [--output run_manifest.json]
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from pipeline.integrity import inventory_supplied_inputs, sha256_file


def _uv_version() -> str:
    executable = shutil.which("uv")
    if executable is None:
        return "unavailable (not on PATH)"
    completed = subprocess.run(
        [executable, "--version"], check=False, capture_output=True, text=True
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable (command failed)"


def _python_version() -> str:
    return sys.version.split()[0]


def _duckdb_version() -> str:
    try:
        import duckdb

        return duckdb.__version__
    except ImportError:
        return "unavailable"


def _artifact(path: Path) -> dict:
    """Return a stable descriptor for a repository artifact."""
    return {
        "path": str(path.relative_to(REPOSITORY_ROOT)),
        "sha256": sha256_file(path),
    }


def _phase1_summary() -> dict:
    """Aggregate Phase 1 evidence from its own manifest."""
    manifest_path = REPOSITORY_ROOT / "data/evidence/phase1/run_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Phase 1 manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "run_id": manifest["run_id"],
        "row_counts": manifest["row_counts"],
        "artifacts": len(manifest.get("artifacts", [])),
        "analyses": len(manifest.get("analyses", [])),
        "source_manifest_sha256": manifest["source_manifest_sha256"],
    }


def _phase2_summary() -> dict:
    """Aggregate Phase 2 KB evidence."""
    eval_path = REPOSITORY_ROOT / "data/evidence/phase2/eval_results.json"
    chunks_path = REPOSITORY_ROOT / "data/evidence/phase2/chunks.jsonl"
    index_path = REPOSITORY_ROOT / "data/evidence/phase2/index.sqlite"

    eval_data = json.loads(eval_path.read_text(encoding="utf-8"))
    chunk_count = sum(1 for _ in chunks_path.open(encoding="utf-8"))

    return {
        "chunks": chunk_count,
        "eval_cases": eval_data["total_cases"],
        "eval_summary": eval_data["summary"]["retrieval_hit_totals"],
        "index_sha256": sha256_file(index_path),
        "chunks_sha256": sha256_file(chunks_path),
    }


def _phase3_summary() -> dict:
    """Aggregate Phase 3 Bedrock trial evidence."""
    preflight_path = REPOSITORY_ROOT / "design/output/preflight_result.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))

    responses_dir = REPOSITORY_ROOT / "design/output/responses"
    response_hashes = {}
    if responses_dir.is_dir():
        for resp_file in sorted(responses_dir.glob("tc*_raw.json")):
            response_hashes[resp_file.name] = sha256_file(resp_file)

    return {
        "model_id": preflight["model_id"],
        "region": preflight["region"],
        "boto3_version": preflight["boto3_version"],
        "trial_pass_rate": "3/5",
        "response_hashes": response_hashes,
    }


def build_manifest() -> dict:
    """Build the consolidated submission manifest payload."""
    source_inventory = inventory_supplied_inputs()

    # Collect all key deliverable paths
    deliverables = []
    deliverable_paths = [
        "README.md",
        "AI_WORKLOG.md",
        "Makefile",
        "pyproject.toml",
        "uv.lock",
        "data/evidence/phase1/run_manifest.json",
        "data/evidence/phase1/quality_ledger.jsonl",
        "data/processed/logs_clean.parquet",
        "data/evidence/phase2/chunks.jsonl",
        "data/evidence/phase2/eval_results.json",
        "data/evidence/phase2/eval_report.md",
        "design/aws_daily_pipeline.md",
        "design/aws_daily_pipeline.png",
        "design/ai_response_review.md",
        "design/extraction_prompt.md",
        "design/output/preflight_result.json",
        "design/output/trial_summary.md",
        "design/output/eval_method.md",
        "sop/kb_update_sop.md",
    ]
    for rel_path in deliverable_paths:
        full_path = REPOSITORY_ROOT / rel_path
        if full_path.is_file():
            deliverables.append(_artifact(full_path))

    commands = {
        "phase1": "make phase1",
        "verify-phase1": "make verify-phase1",
        "phase2": "make phase2",
        "design-report": "make design-report",
        "manifest": "make manifest",
        "audit-submission": "make audit-submission",
        "verify": "make verify",
    }

    payload = {
        "source_inventory": source_inventory,
        "runtime": {
            "python": _python_version(),
            "duckdb": _duckdb_version(),
            "uv": _uv_version(),
        },
        "commands": commands,
        "phases": {
            "phase1_pipeline": _phase1_summary(),
            "phase2_kb": _phase2_summary(),
            "phase3_bedrock": _phase3_summary(),
        },
        "deliverables": sorted(deliverables, key=lambda d: d["path"]),
    }

    run_id = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    return {"run_id": run_id, **payload}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate consolidated submission manifest.")
    parser.add_argument(
        "--output",
        default=str(REPOSITORY_ROOT / "run_manifest.json"),
        help="Output path (default: repo root run_manifest.json)",
    )
    args = parser.parse_args()

    manifest = build_manifest()
    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"manifest written: {output_path} (run_id: {manifest['run_id'][:16]}...)")


if __name__ == "__main__":
    main()
