"""Tests for kb.inventory — document discovery, metadata extraction, and SHA-256 hashing."""

from __future__ import annotations

from pathlib import Path

import pytest

from kb.inventory import inventory_documents
from kb.models import Document

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs/onboard/datapack/data/docs"

EXPECTED_DOC_IDS = {
    "FAQ-01",
    "GUIDE-01",
    "POL-01",  # two files share this doc_id
    "POL-02",
    "RUN-01",
    "SOP-01",
    "SOP-02",
}


def test_inventory_discovers_eight_files() -> None:
    """inventory_documents() returns exactly 8 Document objects from the docs dir."""
    docs = inventory_documents(DOCS_DIR)
    assert len(docs) == 8


def test_inventory_returns_document_objects() -> None:
    """Each item returned is a Document dataclass instance."""
    docs = inventory_documents(DOCS_DIR)
    for doc in docs:
        assert isinstance(doc, Document)


def test_inventory_source_paths_are_absolute() -> None:
    """Each Document.source_path is an absolute path string pointing to an existing file."""
    docs = inventory_documents(DOCS_DIR)
    for doc in docs:
        p = Path(doc.source_path)
        assert p.is_absolute(), f"source_path not absolute: {doc.source_path}"
        assert p.is_file(), f"source_path not a file: {doc.source_path}"


def test_inventory_doc_ids_parsed_from_filename() -> None:
    """doc_id is parsed from the filename prefix (e.g. 'POL-01' from 'POL-01_chinh_sach_backup_v1.md')."""
    docs = inventory_documents(DOCS_DIR)
    parsed_ids = {doc.doc_id for doc in docs}
    # POL-01 appears twice (v1 and v2)
    assert parsed_ids == EXPECTED_DOC_IDS


def test_inventory_pol01_has_two_documents() -> None:
    """POL-01 appears twice — one per version file."""
    docs = inventory_documents(DOCS_DIR)
    pol01_docs = [d for d in docs if d.doc_id == "POL-01"]
    assert len(pol01_docs) == 2


def test_inventory_filename_version_hints() -> None:
    """filename_version_hint is '_v1' or '_v2' for POL-01 files; None for others."""
    docs = inventory_documents(DOCS_DIR)
    by_path = {Path(d.source_path).name: d for d in docs}
    assert by_path["POL-01_chinh_sach_backup_v1.md"].filename_version_hint == "_v1"
    assert by_path["POL-01_chinh_sach_backup_v2.md"].filename_version_hint == "_v2"
    # FAQ-01 has no _v suffix
    faq = by_path["FAQ-01_loi_thuong_gap.md"]
    assert faq.filename_version_hint is None


def test_inventory_sha256_hashes_are_hex_strings() -> None:
    """Each document has a 64-character lowercase hex SHA-256 hash."""
    docs = inventory_documents(DOCS_DIR)
    for doc in docs:
        assert len(doc.sha256) == 64
        assert doc.sha256 == doc.sha256.lower()
        assert all(c in "0123456789abcdef" for c in doc.sha256)


def test_inventory_sha256_differs_per_file() -> None:
    """Each document has a unique SHA-256 (all 8 files are distinct)."""
    docs = inventory_documents(DOCS_DIR)
    hashes = [doc.sha256 for doc in docs]
    assert len(set(hashes)) == 8


def test_inventory_is_deterministic() -> None:
    """Calling inventory_documents twice returns identical ordered results."""
    first = inventory_documents(DOCS_DIR)
    second = inventory_documents(DOCS_DIR)
    assert [d.source_path for d in first] == [d.source_path for d in second]
    assert [d.sha256 for d in first] == [d.sha256 for d in second]


def test_inventory_nonexistent_dir_raises() -> None:
    """inventory_documents raises FileNotFoundError for a missing directory."""
    with pytest.raises(FileNotFoundError):
        inventory_documents(Path("/nonexistent/path/does/not/exist"))
