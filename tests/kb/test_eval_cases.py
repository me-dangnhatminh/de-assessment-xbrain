"""Tests for kb/eval_cases.py — structure, distribution, and reference correctness."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from kb.eval_cases import EVAL_CASES, EvalCase

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_TYPES = frozenset({"direct_lookup", "multi_source", "version_trap", "out_of_scope"})
VALID_MODES = frozenset({"current", "all"})


# ---------------------------------------------------------------------------
# Test 1: EVAL_CASES contains exactly 10 cases
# ---------------------------------------------------------------------------


def test_eval_cases_count():
    assert len(EVAL_CASES) == 10, f"Expected 10 cases, got {len(EVAL_CASES)}"


# ---------------------------------------------------------------------------
# Test 2: Distribution is exactly 4-3-2-1
# ---------------------------------------------------------------------------


def test_eval_cases_type_distribution():
    counts: dict[str, int] = {}
    for case in EVAL_CASES:
        counts[case.question_type] = counts.get(case.question_type, 0) + 1

    assert counts.get("direct_lookup", 0) == 4, f"direct_lookup: {counts}"
    assert counts.get("multi_source", 0) == 3, f"multi_source: {counts}"
    assert counts.get("version_trap", 0) == 2, f"version_trap: {counts}"
    assert counts.get("out_of_scope", 0) == 1, f"out_of_scope: {counts}"


# ---------------------------------------------------------------------------
# Test 3: Each case has all required fields with correct types
# ---------------------------------------------------------------------------


def test_eval_cases_required_fields():
    for case in EVAL_CASES:
        assert isinstance(case, EvalCase), f"{case.case_id} is not EvalCase"
        assert isinstance(case.case_id, str) and case.case_id, "case_id must be non-empty str"
        assert isinstance(case.question, str) and case.question, "question must be non-empty str"
        assert case.question_type in VALID_TYPES, (
            f"{case.case_id}: invalid type {case.question_type!r}"
        )
        assert isinstance(case.query_terms, str) and case.query_terms, (
            f"{case.case_id}: query_terms must be non-empty str"
        )
        assert case.search_mode in VALID_MODES, (
            f"{case.case_id}: invalid search_mode {case.search_mode!r}"
        )
        assert isinstance(case.expected_sources, tuple), (
            f"{case.case_id}: expected_sources must be tuple"
        )
        assert isinstance(case.expected_answer_keywords, tuple), (
            f"{case.case_id}: expected_answer_keywords must be tuple"
        )
        assert isinstance(case.pass_criteria, str) and case.pass_criteria, (
            f"{case.case_id}: pass_criteria must be non-empty str"
        )
        assert isinstance(case.partial_criteria, str) and case.partial_criteria, (
            f"{case.case_id}: partial_criteria must be non-empty str"
        )
        assert isinstance(case.fail_criteria, str) and case.fail_criteria, (
            f"{case.case_id}: fail_criteria must be non-empty str"
        )


# ---------------------------------------------------------------------------
# Test 4: Version-trap cases reference POL-01 and use correct search modes
# ---------------------------------------------------------------------------


def test_version_trap_cases_reference_pol01():
    version_trap_cases = [c for c in EVAL_CASES if c.question_type == "version_trap"]
    assert len(version_trap_cases) == 2

    for case in version_trap_cases:
        # All expected_sources should reference POL-01
        doc_ids = {src[0] for src in case.expected_sources}
        assert "POL-01" in doc_ids, (
            f"{case.case_id}: version_trap case must reference POL-01, got {doc_ids}"
        )

    # Q08 (current retention) should use current mode — returns v2 only
    q08 = next(
        c for c in version_trap_cases if "hiện hành" in c.question.lower() or c.case_id == "Q08"
    )
    assert q08.search_mode == "current", (
        f"{q08.case_id}: retention question should use current mode to prove v2 wins"
    )

    # Q09 (comparison) should use all mode — needs both v1 and v2
    q09 = next(c for c in version_trap_cases if c.case_id == "Q09")
    assert q09.search_mode == "all", (
        f"{q09.case_id}: comparison question should use all mode to expose both versions"
    )


# ---------------------------------------------------------------------------
# Test 5: Out-of-scope case has no expected sources and empty keywords
# ---------------------------------------------------------------------------


def test_out_of_scope_case():
    oos = [c for c in EVAL_CASES if c.question_type == "out_of_scope"]
    assert len(oos) == 1

    case = oos[0]
    assert case.expected_sources == (), (
        f"{case.case_id}: out_of_scope case must have no expected sources"
    )
    assert case.expected_answer_keywords == (), (
        f"{case.case_id}: out_of_scope case must have no expected keywords"
    )
    # Question must not be answerable by the 8 known doc IDs
    text_lower = case.question.lower()
    # Sanity: the question should be about something outside operational docs
    assert (
        "chi phí" in text_lower
        or "cost" in text_lower
        or "price" in text_lower
        or "phí" in text_lower
    ), f"{case.case_id}: expected out-of-scope financial question, got: {case.question!r}"


# ---------------------------------------------------------------------------
# Test 6: Multi-source cases have ≥2 distinct doc_id expected sources
# ---------------------------------------------------------------------------


def test_multi_source_cases_have_multiple_docs():
    ms_cases = [c for c in EVAL_CASES if c.question_type == "multi_source"]
    assert len(ms_cases) == 3

    for case in ms_cases:
        doc_ids = {src[0] for src in case.expected_sources}
        assert len(doc_ids) >= 2, (
            f"{case.case_id}: multi_source case must reference ≥2 doc_ids, got {doc_ids}"
        )


# ---------------------------------------------------------------------------
# Test 7: All expected_sources reference doc_ids that exist in the chunk index
# (requires the built index; skip if not present)
# ---------------------------------------------------------------------------

INDEX_PATH = Path(__file__).resolve().parents[2] / "data" / "evidence" / "phase2" / "index.sqlite"


@pytest.mark.skipif(
    not INDEX_PATH.exists(), reason="index.sqlite not built — run 'make kb-build' first"
)
def test_expected_sources_exist_in_index():
    conn = sqlite3.connect(INDEX_PATH)
    rows = conn.execute("SELECT DISTINCT doc_id FROM chunks_meta").fetchall()
    conn.close()
    indexed_doc_ids = {r[0] for r in rows}

    for case in EVAL_CASES:
        for doc_id, section in case.expected_sources:
            assert doc_id in indexed_doc_ids, (
                f"{case.case_id}: expected source doc_id '{doc_id}' not found in index "
                f"(indexed: {sorted(indexed_doc_ids)})"
            )


@pytest.mark.skipif(
    not INDEX_PATH.exists(), reason="index.sqlite not built — run 'make kb-build' first"
)
def test_expected_source_sections_exist_in_index():
    conn = sqlite3.connect(INDEX_PATH)

    for case in EVAL_CASES:
        for doc_id, section in case.expected_sources:
            rows = conn.execute(
                "SELECT COUNT(*) FROM chunks_meta WHERE doc_id = ? AND section = ?",
                (doc_id, section),
            ).fetchone()
            count = rows[0] if rows else 0
            assert count > 0, (
                f"{case.case_id}: expected source ({doc_id!r}, {section!r}) not found in index"
            )

    conn.close()
