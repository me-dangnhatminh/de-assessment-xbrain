"""Tests for kb/eval_runner.py — execution, scoring, version-trap, and out-of-scope."""

from __future__ import annotations

from pathlib import Path

import pytest

from kb.eval_cases import EVAL_CASES, EvalCase
from kb.eval_runner import EvalResult, run_evaluation, score_groundedness, score_retrieval_hit

INDEX_PATH = Path(__file__).resolve().parents[2] / "data" / "evidence" / "phase2" / "index.sqlite"
SKIP_NO_INDEX = pytest.mark.skipif(
    not INDEX_PATH.exists(), reason="index.sqlite not built — run 'make kb-build' first"
)


# ---------------------------------------------------------------------------
# Unit tests for scoring helpers (no index required)
# ---------------------------------------------------------------------------


class _FakeResult:
    """Minimal stand-in for SearchResult for unit-testing scorers."""

    def __init__(self, doc_id: str, section: str, is_current: bool, content: str = ""):
        self.doc_id = doc_id
        self.section = section
        self.is_current = is_current
        self.content = content


def _make_case(**kwargs) -> EvalCase:
    defaults = {
        "case_id": "TEST",
        "question": "Q?",
        "question_type": "direct_lookup",
        "query_terms": "q",
        "search_mode": "current",
        "expected_sources": (("DOC-01", "Section A"),),
        "expected_answer_keywords": ("keyword1",),
        "pass_criteria": "pass",
        "partial_criteria": "partial",
        "fail_criteria": "fail",
    }
    defaults.update(kwargs)
    return EvalCase(**defaults)


def test_score_retrieval_hit_pass():
    case = _make_case(expected_sources=(("DOC-01", "Section A"),))
    retrieved = [_FakeResult("DOC-01", "Section A", True)]
    score, found = score_retrieval_hit(case, retrieved)
    assert score == "pass"
    assert ("DOC-01", "Section A") in found


def test_score_retrieval_hit_fail():
    case = _make_case(expected_sources=(("DOC-01", "Section A"),))
    retrieved = [_FakeResult("DOC-02", "Other", True)]
    score, _ = score_retrieval_hit(case, retrieved)
    assert score == "fail"


def test_score_retrieval_hit_partial():
    case = _make_case(
        expected_sources=(
            ("DOC-01", "Section A"),
            ("DOC-02", "Section B"),
        )
    )
    retrieved = [_FakeResult("DOC-01", "Section A", True)]
    score, _ = score_retrieval_hit(case, retrieved)
    assert score == "partial"


def test_score_retrieval_hit_out_of_scope_empty():
    case = _make_case(
        question_type="out_of_scope",
        expected_sources=(),
        expected_answer_keywords=(),
    )
    score, found = score_retrieval_hit(case, [])
    assert score == "pass"
    assert found == []


def test_score_retrieval_hit_out_of_scope_non_empty():
    case = _make_case(
        question_type="out_of_scope",
        expected_sources=(),
        expected_answer_keywords=(),
    )
    retrieved = [_FakeResult("DOC-01", "Section A", True, "some content")]
    score, _ = score_retrieval_hit(case, retrieved)
    assert score == "fail"


def test_score_groundedness_pass():
    case = _make_case(expected_answer_keywords=("foo", "bar"))
    retrieved = [_FakeResult("X", "Y", True, content="foo and bar are here")]
    score = score_groundedness(case, retrieved)
    assert score == "pass"


def test_score_groundedness_fail():
    case = _make_case(expected_answer_keywords=("missing",))
    retrieved = [_FakeResult("X", "Y", True, content="nothing relevant")]
    score = score_groundedness(case, retrieved)
    assert score == "fail"


def test_score_groundedness_partial():
    case = _make_case(expected_answer_keywords=("present", "absent"))
    retrieved = [_FakeResult("X", "Y", True, content="only present is here")]
    score = score_groundedness(case, retrieved)
    assert score == "partial"


def test_score_groundedness_out_of_scope_empty():
    case = _make_case(
        question_type="out_of_scope", expected_sources=(), expected_answer_keywords=()
    )
    score = score_groundedness(case, [])
    assert score == "pass"


def test_score_groundedness_out_of_scope_non_empty():
    case = _make_case(
        question_type="out_of_scope", expected_sources=(), expected_answer_keywords=()
    )
    score = score_groundedness(case, [_FakeResult("X", "Y", True, "content")])
    assert score == "fail"


# ---------------------------------------------------------------------------
# Integration tests — require the built index
# ---------------------------------------------------------------------------


@SKIP_NO_INDEX
def test_run_evaluation_returns_ten_results():
    """Test 1: run_evaluation() returns exactly 10 EvalResult objects."""
    results = run_evaluation(INDEX_PATH, EVAL_CASES, top_k=5)
    assert len(results) == 10


@SKIP_NO_INDEX
def test_eval_results_have_required_fields():
    """Test 2: Each EvalResult has all required fields with correct types."""
    results = run_evaluation(INDEX_PATH, EVAL_CASES, top_k=5)
    for r in results:
        assert isinstance(r, EvalResult)
        assert r.case_id
        assert r.question
        assert r.question_type in {"direct_lookup", "multi_source", "version_trap", "out_of_scope"}
        assert r.query_used
        assert r.search_mode in {"current", "all"}
        assert isinstance(r.retrieved_chunks, list)
        assert r.retrieval_hit_score in {"pass", "partial", "fail"}
        assert r.groundedness_score in {"pass", "partial", "fail"}
        assert isinstance(r.diagnosis, str) and r.diagnosis
        assert isinstance(r.expected_sources, list)
        assert isinstance(r.actual_sources_found, list)
        # Check chunk dict shape
        for chunk in r.retrieved_chunks:
            assert "chunk_id" in chunk
            assert "doc_id" in chunk
            assert "section" in chunk
            assert "bm25_score" in chunk
            assert "content_snippet" in chunk
            assert "is_current" in chunk


@SKIP_NO_INDEX
def test_version_trap_q08_current_mode_returns_pol01_v2():
    """Test 3: Version trap Q08 — current-mode search returns POL-01 v2 (not v1)."""
    results = run_evaluation(INDEX_PATH, EVAL_CASES, top_k=5)
    q08 = next(r for r in results if r.case_id == "Q08")

    assert q08.search_mode == "current"
    # Top results must include POL-01 current (v2) chunk
    pol01_current = [c for c in q08.retrieved_chunks if c["doc_id"] == "POL-01" and c["is_current"]]
    assert pol01_current, (
        "Q08: current-mode search must return a POL-01 v2 (is_current=True) chunk. "
        f"Got: {[(c['doc_id'], c['is_current']) for c in q08.retrieved_chunks]}"
    )
    # Retrieval hit should be pass
    assert q08.retrieval_hit_score == "pass", (
        f"Q08 retrieval_hit should be pass, got {q08.retrieval_hit_score}. "
        f"Diagnosis: {q08.diagnosis}"
    )


@SKIP_NO_INDEX
def test_version_trap_q09_all_mode_returns_both_versions():
    """Test 4: Version trap Q09 — all-mode search returns both POL-01 v1 and v2."""
    results = run_evaluation(INDEX_PATH, EVAL_CASES, top_k=10)
    q09 = next(r for r in results if r.case_id == "Q09")

    assert q09.search_mode == "all"
    pol01_current = any(c["doc_id"] == "POL-01" and c["is_current"] for c in q09.retrieved_chunks)
    pol01_superseded = any(
        c["doc_id"] == "POL-01" and not c["is_current"] for c in q09.retrieved_chunks
    )
    assert pol01_current, "Q09: POL-01 v2 (current) must appear in all-mode results"
    assert pol01_superseded, (
        "Q09: POL-01 v1 (superseded) must appear in all-mode results for comparison"
    )


@SKIP_NO_INDEX
def test_out_of_scope_q10_diagnosis():
    """Test 5: Out-of-scope Q10 — diagnosis states 'not found in the supplied documents'."""
    results = run_evaluation(INDEX_PATH, EVAL_CASES, top_k=5)
    q10 = next(r for r in results if r.case_id == "Q10")

    assert q10.question_type == "out_of_scope"
    # Diagnosis must explicitly state information is not in the documents
    diagnosis_lower = q10.diagnosis.lower()
    assert any(
        phrase in diagnosis_lower
        for phrase in [
            "not found",
            "không tìm thấy",
            "not in the supplied",
            "absent from",
        ]
    ), f"Q10 diagnosis must say 'not found'; got: {q10.diagnosis!r}"


@SKIP_NO_INDEX
def test_evaluation_is_deterministic():
    """Test 8: Re-running evaluation against the same index produces identical results."""
    results_a = run_evaluation(INDEX_PATH, EVAL_CASES, top_k=5)
    results_b = run_evaluation(INDEX_PATH, EVAL_CASES, top_k=5)

    for a, b in zip(results_a, results_b):
        assert a.case_id == b.case_id
        assert a.retrieval_hit_score == b.retrieval_hit_score
        assert a.groundedness_score == b.groundedness_score
        assert a.diagnosis == b.diagnosis
        assert len(a.retrieved_chunks) == len(b.retrieved_chunks)
        for ca, cb in zip(a.retrieved_chunks, b.retrieved_chunks):
            assert ca["chunk_id"] == cb["chunk_id"]
            assert ca["bm25_score"] == cb["bm25_score"]
