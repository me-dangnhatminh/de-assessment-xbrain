"""Tests for kb.search — search_current() and search_all() with FTS5 BM25 ranking."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from kb.chunking import chunk_document
from kb.index import build_index
from kb.inventory import inventory_documents
from kb.models import SearchResult
from kb.search import search_all, search_current
from kb.versioning import resolve_versions

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs/onboard/datapack/data/docs"


@pytest.fixture(scope="module")
def index_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build a real FTS5 index once for all search tests."""
    output_dir = tmp_path_factory.mktemp("search_index")
    docs = inventory_documents(DOCS_DIR)
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    all_chunks = resolve_versions(docs, all_chunks)
    db_path, _ = build_index(all_chunks, output_dir)
    return db_path


# ---------------------------------------------------------------------------
# search_current
# ---------------------------------------------------------------------------


def test_search_current_returns_list_of_search_results(index_db: Path) -> None:
    """search_current() returns a list of SearchResult objects."""
    results = search_current(index_db, "sao lưu")
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, SearchResult)


def test_search_current_sao_luu_returns_pol01_v2_only(index_db: Path) -> None:
    """search_current('sao lưu') returns POL-01 chunks — all must be is_current=True."""
    results = search_current(index_db, "sao lưu")
    assert len(results) > 0
    # All returned chunks must be current
    assert all(r.is_current for r in results), (
        "search_current returned at least one non-current chunk"
    )


def test_search_current_excludes_pol01_v1(index_db: Path) -> None:
    """search_current('sao lưu') must not return any POL-01 v1 chunks."""
    results = search_current(index_db, "sao lưu")
    v1_results = [r for r in results if r.doc_id == "POL-01" and r.version == "1.0"]
    assert len(v1_results) == 0, f"Got POL-01 v1 results in current search: {v1_results}"


def test_search_current_includes_pol01_v2(index_db: Path) -> None:
    """search_current('sao lưu') returns at least one POL-01 v2 chunk."""
    results = search_current(index_db, "sao lưu")
    v2_results = [r for r in results if r.doc_id == "POL-01" and r.version == "2.0"]
    assert len(v2_results) > 0, "Expected POL-01 v2 in current backup search results"


def test_search_current_escalation_returns_sop02(index_db: Path) -> None:
    """search_current('escalation') returns at least one chunk from SOP-02."""
    results = search_current(index_db, "escalation")
    sop02 = [r for r in results if r.doc_id == "SOP-02"]
    assert len(sop02) > 0, "Expected SOP-02 result for 'escalation' query"


def test_search_current_empty_query_returns_empty(index_db: Path) -> None:
    """search_current with an unrelated query returns empty list, not an error."""
    results = search_current(index_db, "hoàn toàn không liên quan xyz123")
    assert results == []


def test_search_current_result_fields_complete(index_db: Path) -> None:
    """Each SearchResult from search_current has all required fields populated."""
    results = search_current(index_db, "sao lưu")
    assert len(results) > 0
    for r in results:
        assert r.chunk_id
        assert r.doc_id
        assert r.section
        assert r.content
        assert isinstance(r.bm25_score, float)
        assert r.source_path
        assert isinstance(r.is_current, bool)


def test_search_current_top_k_respected(index_db: Path) -> None:
    """search_current respects the top_k parameter."""
    results = search_current(index_db, "backup", top_k=2)
    assert len(results) <= 2


def test_search_current_results_ranked_by_bm25(index_db: Path) -> None:
    """search_current returns results in ascending BM25 order (lower = more relevant)."""
    results = search_current(index_db, "sao lưu", top_k=5)
    if len(results) >= 2:
        scores = [r.bm25_score for r in results]
        assert scores == sorted(scores), "Results not sorted by ascending BM25 score"


# ---------------------------------------------------------------------------
# search_all
# ---------------------------------------------------------------------------


def test_search_all_returns_list_of_search_results(index_db: Path) -> None:
    """search_all() returns a list of SearchResult objects."""
    results = search_all(index_db, "sao lưu")
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, SearchResult)


def test_search_all_sao_luu_includes_both_pol01_versions(index_db: Path) -> None:
    """search_all('sao lưu') returns chunks from both POL-01 v1 and v2."""
    results = search_all(index_db, "sao lưu")
    versions_found = {r.version for r in results if r.doc_id == "POL-01"}
    assert "1.0" in versions_found, "POL-01 v1 should appear in all-versions search"
    assert "2.0" in versions_found, "POL-01 v2 should appear in all-versions search"


def test_search_all_version_metadata_visible(index_db: Path) -> None:
    """search_all results have version and is_current fields that distinguish v1 from v2."""
    results = search_all(index_db, "sao lưu")
    pol01 = [r for r in results if r.doc_id == "POL-01"]
    assert any(not r.is_current for r in pol01), "Expected at least one superseded POL-01 chunk"
    assert any(r.is_current for r in pol01), "Expected at least one current POL-01 chunk"


def test_search_all_has_more_results_than_current(index_db: Path) -> None:
    """search_all returns >= results compared to search_current for the same query."""
    current = search_current(index_db, "sao lưu", top_k=20)
    all_results = search_all(index_db, "sao lưu", top_k=20)
    assert len(all_results) >= len(current)


def test_search_all_empty_query_returns_empty(index_db: Path) -> None:
    """search_all with an unrelated query returns empty list."""
    results = search_all(index_db, "hoàn toàn không liên quan xyz123")
    assert results == []


# ---------------------------------------------------------------------------
# SQL injection safety
# ---------------------------------------------------------------------------


def test_search_current_uses_parameter_binding(index_db: Path) -> None:
    """search_current with SQL meta-characters does not raise and returns safely."""
    # Would fail if string interpolation were used
    results = search_current(index_db, "'; DROP TABLE chunks_meta; --")
    assert isinstance(results, list)


def test_search_all_uses_parameter_binding(index_db: Path) -> None:
    """search_all with SQL meta-characters does not raise and returns safely."""
    results = search_all(index_db, "'; DROP TABLE chunks_fts; --")
    assert isinstance(results, list)


def test_chunks_meta_still_intact_after_injection_attempt(index_db: Path) -> None:
    """chunks_meta table is unmodified after injection query attempts."""
    search_current(index_db, "'; DROP TABLE chunks_meta; --")
    conn = sqlite3.connect(index_db)
    (count,) = conn.execute("SELECT COUNT(*) FROM chunks_meta").fetchone()
    conn.close()
    assert count > 0
