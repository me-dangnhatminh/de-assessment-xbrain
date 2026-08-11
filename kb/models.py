"""Typed dataclass contracts for the version-aware knowledge base pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    """An inventoried source document with parsed metadata and content hash.

    Fields
    ------
    source_path
        Absolute path to the original Markdown file.
    doc_id
        Document identifier parsed from the filename prefix (e.g. ``POL-01``).
    filename_version_hint
        Version suffix found in the filename (e.g. ``_v1``, ``_v2``), or None.
    sha256
        SHA-256 hex digest of the source file bytes.
    version
        Parsed version string from the bold metadata line (e.g. ``2.0``), or None.
    effective_date
        ISO year-month string parsed from ``Ban hành`` / ``Cập nhật`` (e.g. ``2026-05``), or None.
    department
        Department string from the bold metadata line, or None.
    approver
        Value of ``Người duyệt`` from the bold metadata line, or None.
    supersedes_previous
        True when the metadata line contains ``Thay thế phiên bản trước``.
    """

    source_path: str
    doc_id: str
    filename_version_hint: str | None
    sha256: str
    version: str | None
    effective_date: str | None
    department: str | None
    approver: str | None
    supersedes_previous: bool


@dataclass(frozen=True)
class Chunk:
    """One ##-level section from a document, self-contained with attributed header.

    Fields
    ------
    chunk_id
        Deterministic identifier: ``<doc_id>_<version_or_hint>_chunk<index>``.
    doc_id
        Parent document identifier.
    section
        Text of the ``##`` heading for this chunk.
    chunk_index
        0-based position within the document.
    content
        Full chunk text: ``# `` heading + bold metadata line + section body.
    content_hash
        SHA-256 hex digest of ``content`` encoded as UTF-8.
    version
        Inherited from the parent document, or None.
    effective_date
        Inherited from the parent document, or None.
    owner
        Department string from the parent document, or None.
    is_current
        True when this chunk belongs to the current effective version of its doc_id family.
        Set to True by default; overwritten by ``resolve_versions()``.
    source_path
        Absolute path to the source file.
    """

    chunk_id: str
    doc_id: str
    section: str
    chunk_index: int
    content: str
    content_hash: str
    version: str | None
    effective_date: str | None
    owner: str | None
    is_current: bool
    source_path: str


@dataclass(frozen=True)
class SearchResult:
    """One ranked FTS5 search result with full attribution.

    Fields
    ------
    chunk_id
        Identifier of the matching chunk.
    doc_id
        Parent document identifier.
    section
        Section heading of the chunk.
    version
        Document version string, or None.
    effective_date
        ISO year-month of the document, or None.
    is_current
        True when the chunk belongs to the current effective version.
    content
        Full chunk content (or a display-truncated excerpt).
    bm25_score
        BM25 relevance score from SQLite FTS5 (lower = more relevant).
    source_path
        Absolute path to the source file.
    """

    chunk_id: str
    doc_id: str
    section: str
    version: str | None
    effective_date: str | None
    is_current: bool
    content: str
    bm25_score: float
    source_path: str


@dataclass(frozen=True)
class EvalCase:
    """A single predeclared evaluation question with expected answer metadata."""

    question_id: str
    question: str
    question_type: str  # direct_lookup | multi_source | version_trap | out_of_scope
    query_terms: str
    expected_sources: tuple[str, ...]  # chunk_ids or doc_ids
    expected_answer_facts: tuple[str, ...]


@dataclass(frozen=True)
class EvalResult:
    """Scored outcome for one evaluation case."""

    question_id: str
    query_terms: str
    retrieved_chunks: tuple[dict, ...]
    retrieval_hit: str  # pass | partial | fail
    groundedness_diagnosis: str
    overall_score: str  # pass | partial | fail
    notes: str
