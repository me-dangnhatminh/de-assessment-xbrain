"""Tests for kb.chunking — ##-level chunking with doc header prepend and content hashing."""

from __future__ import annotations

import hashlib
from pathlib import Path

from kb.chunking import chunk_document
from kb.models import Chunk, Document

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs/onboard/datapack/data/docs"


def _make_document(filename: str, doc_id: str, version: str | None = None) -> Document:
    path = DOCS_DIR / filename
    return Document(
        source_path=str(path),
        doc_id=doc_id,
        filename_version_hint=None,
        sha256="deadbeef" * 8,
        version=version,
        effective_date=None,
        department=None,
        approver=None,
        supersedes_previous=False,
    )


def test_pol01_v2_produces_two_chunks() -> None:
    """POL-01 v2 has exactly 2 ## sections (Quy định, Trách nhiệm) → 2 chunks."""
    doc = _make_document("POL-01_chinh_sach_backup_v2.md", "POL-01", "2.0")
    chunks = chunk_document(doc)
    assert len(chunks) == 2


def test_faq01_produces_five_chunks() -> None:
    """FAQ-01 has 5 numbered ## sections → 5 chunks."""
    doc = _make_document("FAQ-01_loi_thuong_gap.md", "FAQ-01")
    chunks = chunk_document(doc)
    assert len(chunks) == 5


def test_chunk_prepends_h1_heading() -> None:
    """Each chunk content starts with the document-level # heading."""
    doc = _make_document("POL-01_chinh_sach_backup_v2.md", "POL-01", "2.0")
    chunks = chunk_document(doc)
    for chunk in chunks:
        assert chunk.content.startswith("# POL-01")


def test_chunk_prepends_metadata_line() -> None:
    """Each chunk content includes the bold metadata line after the # heading."""
    doc = _make_document("POL-01_chinh_sach_backup_v2.md", "POL-01", "2.0")
    chunks = chunk_document(doc)
    for chunk in chunks:
        # The metadata line starts with ** and contains Phòng CNTT
        assert "**" in chunk.content
        assert "CNTT" in chunk.content


def test_chunk_section_field_set() -> None:
    """Each chunk has a non-empty section field matching the ## heading text."""
    doc = _make_document("POL-01_chinh_sach_backup_v2.md", "POL-01", "2.0")
    chunks = chunk_document(doc)
    sections = [c.section for c in chunks]
    assert "Quy định" in sections
    assert "Trách nhiệm" in sections


def test_chunk_index_sequential() -> None:
    """chunk_index values are 0-based sequential integers."""
    doc = _make_document("FAQ-01_loi_thuong_gap.md", "FAQ-01")
    chunks = chunk_document(doc)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_chunk_returns_chunk_objects() -> None:
    """chunk_document() returns a list of Chunk dataclass instances."""
    doc = _make_document("POL-01_chinh_sach_backup_v1.md", "POL-01", "1.0")
    chunks = chunk_document(doc)
    for chunk in chunks:
        assert isinstance(chunk, Chunk)


def test_chunk_content_hash_is_sha256() -> None:
    """Each chunk.content_hash is a 64-character lowercase hex string."""
    doc = _make_document("POL-01_chinh_sach_backup_v2.md", "POL-01", "2.0")
    chunks = chunk_document(doc)
    for chunk in chunks:
        assert len(chunk.content_hash) == 64
        assert chunk.content_hash == chunk.content_hash.lower()


def test_chunk_content_hash_matches_content() -> None:
    """content_hash equals sha256 of the chunk content encoded as UTF-8."""
    doc = _make_document("POL-01_chinh_sach_backup_v2.md", "POL-01", "2.0")
    chunks = chunk_document(doc)
    for chunk in chunks:
        expected = hashlib.sha256(chunk.content.encode("utf-8")).hexdigest()
        assert chunk.content_hash == expected


def test_chunking_is_deterministic() -> None:
    """Calling chunk_document twice on the same doc returns identical chunk records."""
    doc = _make_document("POL-01_chinh_sach_backup_v2.md", "POL-01", "2.0")
    first = chunk_document(doc)
    second = chunk_document(doc)
    for a, b in zip(first, second, strict=True):
        assert a.content == b.content
        assert a.content_hash == b.content_hash
        assert a.section == b.section
        assert a.chunk_index == b.chunk_index


def test_chunk_doc_id_propagated() -> None:
    """chunk.doc_id matches the parent document's doc_id."""
    doc = _make_document("FAQ-01_loi_thuong_gap.md", "FAQ-01")
    chunks = chunk_document(doc)
    for chunk in chunks:
        assert chunk.doc_id == "FAQ-01"


def test_chunk_source_path_propagated() -> None:
    """chunk.source_path matches the parent document's source_path."""
    doc = _make_document("POL-01_chinh_sach_backup_v2.md", "POL-01", "2.0")
    chunks = chunk_document(doc)
    for chunk in chunks:
        assert chunk.source_path == doc.source_path


def test_no_section_document_produces_one_chunk() -> None:
    """A document with no ## sections produces exactly 1 chunk containing the full body."""
    # Create a temporary document-like object with content lacking ## headings
    # We'll test this via a synthetic Document with a temp file
    import tempfile

    content = (
        "# FAKE-01 — Only a title\n\n**Meta** · Phiên bản 1.0\n\nSome body text with no sections.\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    doc = Document(
        source_path=tmp_path,
        doc_id="FAKE-01",
        filename_version_hint=None,
        sha256="abc" * 21 + "d",
        version="1.0",
        effective_date=None,
        department=None,
        approver=None,
        supersedes_previous=False,
    )
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert "Some body text with no sections." in chunks[0].content
