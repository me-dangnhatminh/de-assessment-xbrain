"""Render evaluation results to JSON and Markdown report formats.

``render_eval_report(results, output_dir)``
    Writes two files to *output_dir*:
    - ``eval_results.json``  — structured JSON with full metadata
    - ``eval_report.md``     — human-readable Markdown with per-case sections
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from kb.eval_runner import EvalResult

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Score → emoji for the Markdown report
# ---------------------------------------------------------------------------

_SCORE_ICON = {"pass": "✅", "partial": "⚠️", "fail": "❌"}


def _score_icon(score: str) -> str:
    return _SCORE_ICON.get(score, "❓")


# ---------------------------------------------------------------------------
# JSON serialisation
# ---------------------------------------------------------------------------


def render_eval_json(
    results: list[EvalResult],
    db_path: Path,
    output_dir: Path,
    top_k: int,
) -> Path:
    """Write ``eval_results.json`` to *output_dir*.

    Returns the path of the written file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "eval_results.json"

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "index_path": str(db_path.relative_to(REPOSITORY_ROOT))
        if db_path.is_relative_to(REPOSITORY_ROOT)
        else str(db_path),
        "top_k": top_k,
        "total_cases": len(results),
        "summary": _summary_stats(results),
        "results": [_result_to_dict(r) for r in results],
    }

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def _result_to_dict(r: EvalResult) -> dict:
    return {
        "case_id": r.case_id,
        "question": r.question,
        "question_type": r.question_type,
        "query_used": r.query_used,
        "search_mode": r.search_mode,
        "retrieval_hit_score": r.retrieval_hit_score,
        "groundedness_score": r.groundedness_score,
        "diagnosis": r.diagnosis,
        "expected_sources": [list(s) for s in r.expected_sources],
        "actual_sources_found": [list(s) for s in r.actual_sources_found],
        "retrieved_chunks": r.retrieved_chunks,
    }


def _summary_stats(results: list[EvalResult]) -> dict:
    scores = {"pass": 0, "partial": 0, "fail": 0}
    for r in results:
        scores[r.retrieval_hit_score] = scores.get(r.retrieval_hit_score, 0) + 1
    by_type: dict[str, dict[str, int]] = {}
    for r in results:
        t = r.question_type
        if t not in by_type:
            by_type[t] = {"pass": 0, "partial": 0, "fail": 0}
        by_type[t][r.retrieval_hit_score] = by_type[t].get(r.retrieval_hit_score, 0) + 1
    return {
        "retrieval_hit_totals": scores,
        "by_question_type": by_type,
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def render_eval_report(
    results: list[EvalResult],
    db_path: Path,
    output_dir: Path,
    top_k: int,
) -> Path:
    """Write ``eval_report.md`` to *output_dir*.

    Returns the path of the written file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "eval_report.md"

    lines: list[str] = []

    # Header
    lines += [
        "# KB Evaluation Report",
        "",
        f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Index:** `{db_path.relative_to(REPOSITORY_ROOT) if db_path.is_relative_to(REPOSITORY_ROOT) else db_path}`  ",
        f"**Top-k:** {top_k}  ",
        f"**Total cases:** {len(results)}",
        "",
    ]

    # Summary table
    stats = _summary_stats(results)
    totals = stats["retrieval_hit_totals"]
    lines += [
        "## Summary",
        "",
        "| Retrieval Hit | Count |",
        "|---|---|",
        f"| ✅ Pass | {totals.get('pass', 0)} |",
        f"| ⚠️ Partial | {totals.get('partial', 0)} |",
        f"| ❌ Fail | {totals.get('fail', 0)} |",
        "",
        "| Question Type | Pass | Partial | Fail |",
        "|---|---|---|---|",
    ]
    for qtype in ["direct_lookup", "multi_source", "version_trap", "out_of_scope"]:
        bt = stats["by_question_type"].get(qtype, {})
        lines.append(
            f"| {qtype} | {bt.get('pass', 0)} | {bt.get('partial', 0)} | {bt.get('fail', 0)} |"
        )
    lines.append("")

    # Per-case sections
    lines.append("---")
    lines.append("")
    lines.append("## Case Results")
    lines.append("")

    for r in results:
        rh_icon = _score_icon(r.retrieval_hit_score)
        gs_icon = _score_icon(r.groundedness_score)
        lines += [
            f"### {r.case_id} — {r.question_type}",
            "",
            f"**Question:** {r.question}",
            "",
            f"**Query submitted:** `{r.query_used}`  ",
            f"**Search mode:** `{r.search_mode}`",
            "",
            f"**Retrieval hit:** {rh_icon} `{r.retrieval_hit_score}`  ",
            f"**Groundedness:** {gs_icon} `{r.groundedness_score}`",
            "",
        ]

        # Expected sources
        if r.expected_sources:
            lines.append("**Expected sources:**")
            for doc_id, section in r.expected_sources:
                lines.append(f"- `{doc_id}` § {section}")
            lines.append("")

        # Retrieved chunks
        if r.retrieved_chunks:
            lines += [
                f"**Retrieved chunks (top {len(r.retrieved_chunks)}):**",
                "",
                "| Rank | chunk_id | is_current | bm25 | snippet |",
                "|---|---|---|---|---|",
            ]
            for i, chunk in enumerate(r.retrieved_chunks, 1):
                current_flag = "✅" if chunk["is_current"] else "⬛ superseded"
                snippet = chunk["content_snippet"].replace("\n", " ").replace("|", "\\|")[:120]
                lines.append(
                    f"| {i} | `{chunk['chunk_id']}` | {current_flag} | "
                    f"`{chunk['bm25_score']:.4f}` | {snippet}… |"
                )
            lines.append("")
        else:
            lines += ["**Retrieved chunks:** *(none — query returned no results)*", ""]

        lines += [
            "**Diagnosis:**",
            "",
            f"> {r.diagnosis}",
            "",
            "---",
            "",
        ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
