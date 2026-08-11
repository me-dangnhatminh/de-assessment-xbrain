"""Programmatic evaluation executor for the version-aware knowledge base.

``run_evaluation(db_path, cases, top_k=5)``
    Executes all evaluation cases against the FTS5 index, returning one
    ``EvalResult`` per case.  No LLM calls — retrieval-only (KB-09, KB-10).

Scoring dimensions (D-12):
  - ``retrieval_hit``: pass/partial/fail based on whether expected source
    doc_ids and sections appear in the ranked top-k results.
  - ``groundedness``: pass/partial/fail based on whether expected answer
    keywords appear in the content of retrieved chunks.

Both dimensions are scored independently; neither implies the other.

Search mode (D-11):
  - "current" → ``search_current()`` — is_current=1 filter
  - "all"     → ``search_all()``     — all versions including superseded
  - "none"    → empty result set (for out_of_scope cases the search is still
    attempted with "current" mode; a high-relevance result would be a failure)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kb.eval_cases import EvalCase
from kb.search import search_all, search_current

# ---------------------------------------------------------------------------
# EvalResult dataclass
# ---------------------------------------------------------------------------


@dataclass
class EvalResult:
    """Scored outcome for one evaluation case.

    Fields
    ------
    case_id
        Identifier matching the source EvalCase.
    question
        The evaluation question text.
    question_type
        One of: direct_lookup | multi_source | version_trap | out_of_scope.
    query_used
        The query_terms submitted to the search function.
    search_mode
        "current" or "all" as used for this case.
    retrieved_chunks
        List of dicts with chunk_id, doc_id, section, version, effective_date,
        is_current, bm25_score, and content_snippet (first 300 chars).
    expected_sources
        List of (doc_id, section) pairs from the EvalCase.
    actual_sources_found
        List of (doc_id, section) pairs that appeared in retrieved_chunks.
    retrieval_hit_score
        "pass" | "partial" | "fail" based on source coverage.
    groundedness_score
        "pass" | "partial" | "fail" based on keyword presence.
    diagnosis
        Human-readable explanation of the scores and what was found / missing.
    """

    case_id: str
    question: str
    question_type: str
    query_used: str
    search_mode: str
    retrieved_chunks: list[dict]
    expected_sources: list[tuple[str, str]]
    actual_sources_found: list[tuple[str, str]]
    retrieval_hit_score: str
    groundedness_score: str
    diagnosis: str


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def score_retrieval_hit(
    case: EvalCase,
    retrieved: list,
) -> tuple[str, list[tuple[str, str]]]:
    """Score retrieval hit for a case.

    Returns (score, actual_sources_found) where score is "pass"/"partial"/"fail".

    Rules:
    - out_of_scope: pass when no chunk appears (empty result is correct);
      fail when any chunk is returned (would indicate false relevance).
    - All other types: match by (doc_id, section) — every expected source that
      appears anywhere in top-k contributes.  Pass when all expected sources
      are found; partial when ≥1 but not all; fail when none.
    """
    if case.question_type == "out_of_scope":
        if not retrieved:
            return "pass", []
        # Some chunks returned — they may be low-relevance noise.
        # Classify as fail to be conservative: no answer should be implied.
        actual = [(r.doc_id, r.section) for r in retrieved]
        return "fail", actual

    expected = set(case.expected_sources)
    if not expected:
        # No sources declared — trivially pass (shouldn't happen outside out_of_scope)
        return "pass", []

    actual_pairs = [(r.doc_id, r.section) for r in retrieved]
    found = {pair for pair in actual_pairs if pair in expected}

    if found == expected:
        return "pass", list(actual_pairs)
    elif found:
        return "partial", list(actual_pairs)
    else:
        return "fail", list(actual_pairs)


def score_groundedness(
    case: EvalCase,
    retrieved: list,
) -> str:
    """Score groundedness by checking expected_answer_keywords in retrieved content.

    Returns "pass" | "partial" | "fail".

    Rules:
    - out_of_scope with empty result: pass (nothing to check; correct outcome).
    - out_of_scope with non-empty result: fail (content was returned when none expected).
    - Other types with no keywords declared: "pass" (nothing to verify).
    - Other types: pass when all keywords found in combined content;
      partial when ≥1 but not all; fail when none.
    """
    if case.question_type == "out_of_scope":
        return "pass" if not retrieved else "fail"

    keywords = case.expected_answer_keywords
    if not keywords:
        return "pass"

    combined = " ".join(r.content for r in retrieved)
    found = [kw for kw in keywords if kw in combined]

    if len(found) == len(keywords):
        return "pass"
    elif found:
        return "partial"
    else:
        return "fail"


def _build_diagnosis(
    case: EvalCase,
    retrieved: list,
    retrieval_hit: str,
    groundedness: str,
    actual_sources: list[tuple[str, str]],
) -> str:
    """Generate a human-readable diagnosis string."""
    if case.question_type == "out_of_scope":
        if not retrieved:
            return (
                "Not found in the supplied documents. "
                "No relevant chunks retrieved — correct outcome for out-of-scope question."
            )
        else:
            doc_ids = {r.doc_id for r in retrieved}
            return (
                f"Out-of-scope question returned {len(retrieved)} chunk(s) from {sorted(doc_ids)}. "
                "These chunks do not contain the requested information (cost/pricing data absent "
                "from all 8 supplied documents). Retrieval scored fail."
            )

    parts: list[str] = []

    # Retrieval hit diagnosis
    expected_set = set(case.expected_sources)
    actual_set = set(actual_sources)
    matched = expected_set & actual_set
    missing = expected_set - actual_set

    if retrieval_hit == "pass":
        parts.append(
            f"Retrieval hit PASS: all {len(expected_set)} expected source(s) found in top-k."
        )
    elif retrieval_hit == "partial":
        parts.append(
            f"Retrieval hit PARTIAL: {len(matched)}/{len(expected_set)} expected source(s) found. "
            f"Missing: {sorted(str(s) for s in missing)}."
        )
    else:
        parts.append(
            f"Retrieval hit FAIL: 0/{len(expected_set)} expected source(s) found in top-k. "
            f"Expected: {sorted(str(s) for s in expected_set)}."
        )

    # Groundedness diagnosis
    keywords = case.expected_answer_keywords
    if keywords:
        combined = " ".join(r.content for r in retrieved)
        found_kw = [kw for kw in keywords if kw in combined]
        missing_kw = [kw for kw in keywords if kw not in combined]
        if groundedness == "pass":
            parts.append(
                f"Groundedness PASS: all {len(keywords)} keyword(s) present in retrieved content."
            )
        elif groundedness == "partial":
            parts.append(
                f"Groundedness PARTIAL: {len(found_kw)}/{len(keywords)} keyword(s) found. "
                f"Missing: {missing_kw}."
            )
        else:
            parts.append(
                f"Groundedness FAIL: 0/{len(keywords)} keyword(s) found in retrieved content. "
                f"Expected: {list(keywords)}."
            )
    else:
        parts.append("Groundedness: no keywords declared — skipped.")

    # Version-trap specific note
    if case.question_type == "version_trap" and case.search_mode == "current":
        pol01_v2 = any(r.doc_id == "POL-01" and r.is_current for r in retrieved)
        pol01_v1 = any(r.doc_id == "POL-01" and not r.is_current for r in retrieved)
        if pol01_v2 and not pol01_v1:
            parts.append(
                "Version trap: POL-01 v2 (current) returned; superseded v1 correctly excluded."
            )
        elif pol01_v1 and not pol01_v2:
            parts.append(
                "Version trap WARNING: only superseded POL-01 v1 returned — v2 policy missed."
            )
        elif pol01_v2 and pol01_v1:
            parts.append(
                "Version trap: both v1 and v2 returned — current mode returned a superseded chunk."
            )

    if case.question_type == "version_trap" and case.search_mode == "all":
        pol01_v2 = any(r.doc_id == "POL-01" and r.is_current for r in retrieved)
        pol01_v1 = any(r.doc_id == "POL-01" and not r.is_current for r in retrieved)
        if pol01_v2 and pol01_v1:
            parts.append(
                "Version trap (comparison): both POL-01 v1 (superseded) and v2 (current) retrieved "
                "— full version history available for comparison."
            )
        elif not pol01_v1:
            parts.append(
                "Version trap WARNING: POL-01 v1 (superseded) not retrieved — comparison incomplete."
            )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main evaluation runner
# ---------------------------------------------------------------------------


def run_evaluation(
    db_path: Path,
    cases: list[EvalCase],
    top_k: int = 5,
) -> list[EvalResult]:
    """Execute all evaluation cases against the FTS5 index.

    Parameters
    ----------
    db_path:
        Path to the SQLite index built by :func:`kb.index.build_index`.
    cases:
        List of :class:`kb.eval_cases.EvalCase` to evaluate.
    top_k:
        Number of ranked results to retrieve per case (default 5).

    Returns
    -------
    List of :class:`EvalResult` objects, one per input case, in the same order.
    """
    results: list[EvalResult] = []

    for case in cases:
        # Dispatch to the appropriate search function based on declared mode
        if case.search_mode == "all":
            retrieved = search_all(db_path, case.query_terms, top_k=top_k)
        else:
            # "current" (default for all non-all cases, including out_of_scope)
            retrieved = search_current(db_path, case.query_terms, top_k=top_k)

        # Score both dimensions independently
        retrieval_hit, actual_sources = score_retrieval_hit(case, retrieved)
        groundedness = score_groundedness(case, retrieved)

        diagnosis = _build_diagnosis(case, retrieved, retrieval_hit, groundedness, actual_sources)

        # Serialize chunks for the result record
        chunk_dicts = [
            {
                "chunk_id": r.chunk_id,
                "doc_id": r.doc_id,
                "section": r.section,
                "version": r.version,
                "effective_date": r.effective_date,
                "is_current": r.is_current,
                "bm25_score": r.bm25_score,
                "content_snippet": r.content[:300],
            }
            for r in retrieved
        ]

        results.append(
            EvalResult(
                case_id=case.case_id,
                question=case.question,
                question_type=case.question_type,
                query_used=case.query_terms,
                search_mode=case.search_mode,
                retrieved_chunks=chunk_dicts,
                expected_sources=list(case.expected_sources),
                actual_sources_found=actual_sources,
                retrieval_hit_score=retrieval_hit,
                groundedness_score=groundedness,
                diagnosis=diagnosis,
            )
        )

    return results
