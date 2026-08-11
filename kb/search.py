"""FTS5 search functions for the version-aware knowledge base.

Two public functions:

``search_current(db_path, query, top_k=5)``
    Filter to ``is_current=1`` chunks before FTS5 ranking (D-09).
    Returns policy-effective results only.

``search_all(db_path, query, top_k=10)``
    No is_current filter — returns results across all versions.
    Use this for historical provenance inspection (KB-11).

Both functions use SQLite parameter binding exclusively — no string
interpolation in SQL.  BM25 scores are returned as-is (lower = more relevant
in SQLite's sign convention).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from kb.models import SearchResult

# ---------------------------------------------------------------------------
# SQL templates — parameterised with ? placeholders only (T-02-01 mitigation)
# ---------------------------------------------------------------------------

# FTS5 MATCH with is_current filter, ranked by bm25 ascending (more relevant first)
_SQL_SEARCH_CURRENT = """
SELECT
    m.chunk_id,
    m.doc_id,
    m.section,
    m.version,
    m.effective_date,
    m.is_current,
    m.content,
    bm25(chunks_fts) AS score,
    m.source_path
FROM chunks_fts
JOIN chunks_meta AS m ON chunks_fts.rowid = m.rowid
WHERE chunks_fts MATCH ?
  AND m.is_current = 1
ORDER BY score
LIMIT ?
"""

# FTS5 MATCH without is_current filter
_SQL_SEARCH_ALL = """
SELECT
    m.chunk_id,
    m.doc_id,
    m.section,
    m.version,
    m.effective_date,
    m.is_current,
    m.content,
    bm25(chunks_fts) AS score,
    m.source_path
FROM chunks_fts
JOIN chunks_meta AS m ON chunks_fts.rowid = m.rowid
WHERE chunks_fts MATCH ?
ORDER BY score
LIMIT ?
"""


def _rows_to_results(rows: list[tuple]) -> list[SearchResult]:
    """Convert raw sqlite3 row tuples to SearchResult dataclasses."""
    results = []
    for row in rows:
        (
            chunk_id,
            doc_id,
            section,
            version,
            effective_date,
            is_current,
            content,
            score,
            source_path,
        ) = row
        results.append(
            SearchResult(
                chunk_id=chunk_id,
                doc_id=doc_id,
                section=section,
                version=version,
                effective_date=effective_date,
                is_current=bool(is_current),
                content=content,
                bm25_score=float(score),
                source_path=source_path,
            )
        )
    return results


def _safe_fts_query(query: str) -> str | None:
    """Sanitise a user query for FTS5 MATCH.

    FTS5 MATCH raises OperationalError on empty strings and may misinterpret
    raw punctuation as query syntax.  Wrapping the query in double-quotes
    treats it as a phrase search and safely handles most punctuation.
    Returns None when the query is empty/whitespace-only (caller returns []).
    """
    stripped = query.strip()
    if not stripped:
        return None
    # Escape internal double-quotes by doubling them, then wrap in outer quotes
    escaped = stripped.replace('"', '""')
    return f'"{escaped}"'


def search_current(db_path: Path, query: str, top_k: int = 5) -> list[SearchResult]:
    """Return the top-k current-policy chunks matching *query*, ranked by BM25.

    Parameters
    ----------
    db_path:
        Path to the SQLite index built by :func:`kb.index.build_index`.
    query:
        Free-text search query in the original document language (Vietnamese).
    top_k:
        Maximum number of results to return (default 5).

    Returns
    -------
    List of :class:`SearchResult` objects sorted ascending by BM25 score
    (lower = more relevant).  Empty list when no match is found.
    """
    safe_q = _safe_fts_query(query)
    if safe_q is None:
        return []
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute(_SQL_SEARCH_CURRENT, (safe_q, top_k)).fetchall()
        conn.close()
    except sqlite3.OperationalError:
        # Malformed query syntax after sanitisation → return empty
        return []
    return _rows_to_results(rows)


def search_all(db_path: Path, query: str, top_k: int = 10) -> list[SearchResult]:
    """Return the top-k chunks matching *query* across all versions, ranked by BM25.

    Parameters
    ----------
    db_path:
        Path to the SQLite index built by :func:`kb.index.build_index`.
    query:
        Free-text search query in the original document language (Vietnamese).
    top_k:
        Maximum number of results to return (default 10).

    Returns
    -------
    List of :class:`SearchResult` objects sorted ascending by BM25 score.
    Superseded chunks are included; inspect ``is_current`` to distinguish them.
    Empty list when no match is found.
    """
    safe_q = _safe_fts_query(query)
    if safe_q is None:
        return []
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute(_SQL_SEARCH_ALL, (safe_q, top_k)).fetchall()
        conn.close()
    except sqlite3.OperationalError:
        return []
    return _rows_to_results(rows)
