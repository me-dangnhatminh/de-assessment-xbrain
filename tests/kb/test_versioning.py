"""Tests for kb.versioning — deterministic is_current resolution across doc_id families."""

from __future__ import annotations

from kb.models import Chunk, Document
from kb.versioning import resolve_versions

# ---------------------------------------------------------------------------
# Helpers to build minimal Document and Chunk fixtures
# ---------------------------------------------------------------------------


def _doc(
    doc_id: str,
    version: str | None,
    effective_date: str | None,
    supersedes_previous: bool = False,
    source_path: str | None = None,
) -> Document:
    # Each unique (doc_id, version) pair gets a distinct synthetic path so that
    # resolve_versions() can distinguish documents within the same family.
    if source_path is None:
        safe_ver = (version or "none").replace(".", "_")
        source_path = f"/fake/{doc_id}_{safe_ver}.md"
    return Document(
        source_path=source_path,
        doc_id=doc_id,
        filename_version_hint=None,
        sha256="a" * 64,
        version=version,
        effective_date=effective_date,
        department=None,
        approver=None,
        supersedes_previous=supersedes_previous,
    )


def _chunk(doc: Document, index: int = 0) -> Chunk:
    return Chunk(
        chunk_id=f"{doc.doc_id}_{doc.version or 'v0'}_chunk{index}",
        doc_id=doc.doc_id,
        section="Section",
        chunk_index=index,
        content="content",
        content_hash="b" * 64,
        version=doc.version,
        effective_date=doc.effective_date,
        owner=doc.department,
        is_current=True,  # default — resolve_versions() will overwrite
        source_path=doc.source_path,
    )


# ---------------------------------------------------------------------------
# POL-01 supersession tests
# ---------------------------------------------------------------------------


def test_pol01_v2_supersession_phrase_makes_v2_current() -> None:
    """POL-01 v2 with supersedes_previous=True → is_current=True."""
    doc_v1 = _doc("POL-01", "1.0", "2025-06", supersedes_previous=False)
    doc_v2 = _doc("POL-01", "2.0", "2026-05", supersedes_previous=True)
    chunk_v1 = _chunk(doc_v1)
    chunk_v2 = _chunk(doc_v2)

    result = resolve_versions([doc_v1, doc_v2], [chunk_v1, chunk_v2])
    by_version = {c.version: c for c in result}

    assert by_version["2.0"].is_current is True
    assert by_version["1.0"].is_current is False


def test_pol01_v1_superseded_all_chunks() -> None:
    """All POL-01 v1 chunks are marked is_current=False when v2 supersedes."""
    doc_v1 = _doc("POL-01", "1.0", "2025-06", supersedes_previous=False)
    doc_v2 = _doc("POL-01", "2.0", "2026-05", supersedes_previous=True)
    # Two chunks per version
    chunks = [_chunk(doc_v1, 0), _chunk(doc_v1, 1), _chunk(doc_v2, 0), _chunk(doc_v2, 1)]

    result = resolve_versions([doc_v1, doc_v2], chunks)
    v1_chunks = [c for c in result if c.version == "1.0"]
    v2_chunks = [c for c in result if c.version == "2.0"]

    assert all(not c.is_current for c in v1_chunks)
    assert all(c.is_current for c in v2_chunks)


def test_sole_version_docs_always_current() -> None:
    """Documents with no sibling in their doc_id family are always is_current=True."""
    doc_faq = _doc("FAQ-01", None, "2026-07")
    doc_sop = _doc("SOP-01", None, "2026-03")
    docs = [doc_faq, doc_sop]
    chunks = [_chunk(doc_faq), _chunk(doc_sop)]

    result = resolve_versions(docs, chunks)
    assert all(c.is_current for c in result)


def test_effective_date_fallback_latest_wins() -> None:
    """Without a supersession phrase, the document with the latest effective_date wins."""
    doc_old = _doc("HYPO-01", "1.0", "2024-01", supersedes_previous=False)
    doc_new = _doc("HYPO-01", "2.0", "2025-06", supersedes_previous=False)
    chunks = [_chunk(doc_old), _chunk(doc_new)]

    result = resolve_versions([doc_old, doc_new], chunks)
    by_version = {c.version: c for c in result}

    assert by_version["2.0"].is_current is True
    assert by_version["1.0"].is_current is False


def test_effective_date_fallback_earlier_loses() -> None:
    """The older doc_date document is marked is_current=False in the fallback path."""
    doc_a = _doc("HYPO-02", "1.0", "2023-01", supersedes_previous=False)
    doc_b = _doc("HYPO-02", "1.1", "2024-11", supersedes_previous=False)
    chunks = [_chunk(doc_a), _chunk(doc_b)]

    result = resolve_versions([doc_a, doc_b], chunks)
    by_version = {c.version: c for c in result}

    assert by_version["1.1"].is_current is True
    assert by_version["1.0"].is_current is False


def test_resolve_versions_returns_all_chunks() -> None:
    """resolve_versions returns the same number of chunks as input."""
    doc_v1 = _doc("POL-01", "1.0", "2025-06")
    doc_v2 = _doc("POL-01", "2.0", "2026-05", supersedes_previous=True)
    chunks = [_chunk(doc_v1, i) for i in range(3)] + [_chunk(doc_v2, i) for i in range(2)]

    result = resolve_versions([doc_v1, doc_v2], chunks)
    assert len(result) == 5


def test_resolve_versions_mixed_families() -> None:
    """POL-01 supersession does not affect other doc_id families."""
    doc_pol_v1 = _doc("POL-01", "1.0", "2025-06")
    doc_pol_v2 = _doc("POL-01", "2.0", "2026-05", supersedes_previous=True)
    doc_sop = _doc("SOP-01", None, "2026-03")
    all_docs = [doc_pol_v1, doc_pol_v2, doc_sop]
    all_chunks = [_chunk(doc_pol_v1), _chunk(doc_pol_v2), _chunk(doc_sop)]

    result = resolve_versions(all_docs, all_chunks)
    by_doc = {c.doc_id: [] for c in result}
    for c in result:
        by_doc[c.doc_id].append(c)

    # SOP-01 stays current
    assert all(c.is_current for c in by_doc["SOP-01"])
    # POL-01 v1 superseded, v2 current
    pol_by_ver = {c.version: c for c in by_doc["POL-01"]}
    assert pol_by_ver["1.0"].is_current is False
    assert pol_by_ver["2.0"].is_current is True
