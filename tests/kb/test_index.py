"""Tests for kb.index — FTS5 preflight, schema creation, chunk insertion, and chunks.jsonl export."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from kb.chunking import chunk_document
from kb.index import FTS5NotAvailableError, build_index, check_fts5
from kb.inventory import inventory_documents
from kb.models import Chunk
from kb.versioning import resolve_versions

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs/onboard/datapack/data/docs"


# ---------------------------------------------------------------------------
# FTS5 preflight
# ---------------------------------------------------------------------------


def test_fts5_available_on_this_machine() -> None:
    """SQLite FTS5 is compiled in on the test machine — preflight passes."""
    assert check_fts5() is True


def test_fts5_check_returns_bool() -> None:
    """check_fts5() returns a bool, not a truthy object."""
    result = check_fts5()
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# build_index schema and row count
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def built_index(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """Build index once for all schema/row-count tests."""
    output_dir = tmp_path_factory.mktemp("phase2")
    docs = inventory_documents(DOCS_DIR)
    all_chunks: list[Chunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    all_chunks = resolve_versions(docs, all_chunks)
    db_path, jsonl_path = build_index(all_chunks, output_dir)
    return {
        "db_path": db_path,
        "jsonl_path": jsonl_path,
        "chunks": all_chunks,
        "output_dir": output_dir,
    }


def test_build_index_creates_sqlite_file(built_index: dict) -> None:
    """build_index() creates index.sqlite in the output directory."""
    assert built_index["db_path"].is_file()
    assert built_index["db_path"].name == "index.sqlite"


def test_build_index_creates_chunks_jsonl(built_index: dict) -> None:
    """build_index() creates chunks.jsonl in the output directory."""
    assert built_index["jsonl_path"].is_file()
    assert built_index["jsonl_path"].name == "chunks.jsonl"


def test_chunks_meta_table_exists(built_index: dict) -> None:
    """The chunks_meta normal table is present in the database."""
    conn = sqlite3.connect(built_index["db_path"])
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks_meta'")
    assert cur.fetchone() is not None
    conn.close()


def test_chunks_fts_table_exists(built_index: dict) -> None:
    """The chunks_fts FTS5 virtual table is present in the database."""
    conn = sqlite3.connect(built_index["db_path"])
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks_fts'")
    assert cur.fetchone() is not None
    conn.close()


def test_chunks_meta_has_required_columns(built_index: dict) -> None:
    """chunks_meta has all required columns."""
    required = {
        "chunk_id",
        "doc_id",
        "section",
        "version",
        "effective_date",
        "owner",
        "status",
        "content_hash",
        "is_current",
        "source_path",
        "chunk_index",
    }
    conn = sqlite3.connect(built_index["db_path"])
    cur = conn.execute("PRAGMA table_info(chunks_meta)")
    columns = {row[1] for row in cur.fetchall()}
    conn.close()
    assert required.issubset(columns), f"missing columns: {required - columns}"


def test_row_count_matches_chunks(built_index: dict) -> None:
    """chunks_meta row count equals the total chunk count from all 8 documents."""
    conn = sqlite3.connect(built_index["db_path"])
    (count,) = conn.execute("SELECT COUNT(*) FROM chunks_meta").fetchone()
    conn.close()
    assert count == len(built_index["chunks"])


def test_pol01_v2_is_current_in_db(built_index: dict) -> None:
    """POL-01 v2 rows have is_current=1 in chunks_meta."""
    conn = sqlite3.connect(built_index["db_path"])
    rows = conn.execute(
        "SELECT is_current FROM chunks_meta WHERE doc_id='POL-01' AND version='2.0'"
    ).fetchall()
    conn.close()
    assert len(rows) > 0
    assert all(row[0] == 1 for row in rows)


def test_pol01_v1_not_current_in_db(built_index: dict) -> None:
    """POL-01 v1 rows have is_current=0 in chunks_meta."""
    conn = sqlite3.connect(built_index["db_path"])
    rows = conn.execute(
        "SELECT is_current FROM chunks_meta WHERE doc_id='POL-01' AND version='1.0'"
    ).fetchall()
    conn.close()
    assert len(rows) > 0
    assert all(row[0] == 0 for row in rows)


# ---------------------------------------------------------------------------
# chunks.jsonl determinism
# ---------------------------------------------------------------------------


def test_chunks_jsonl_is_valid_jsonl(built_index: dict) -> None:
    """Every line in chunks.jsonl parses as valid JSON."""
    lines = built_index["jsonl_path"].read_text(encoding="utf-8").splitlines()
    assert len(lines) > 0
    for line in lines:
        obj = json.loads(line)
        assert isinstance(obj, dict)


def test_chunks_jsonl_has_all_required_fields(built_index: dict) -> None:
    """Each JSONL record contains the full set of chunk fields."""
    required = {
        "chunk_id",
        "doc_id",
        "section",
        "chunk_index",
        "content",
        "content_hash",
        "version",
        "effective_date",
        "owner",
        "is_current",
        "source_path",
    }
    lines = built_index["jsonl_path"].read_text(encoding="utf-8").splitlines()
    for line in lines:
        obj = json.loads(line)
        assert required.issubset(obj.keys()), f"missing keys in: {obj['chunk_id']}"


def test_chunks_jsonl_line_count_matches_chunks(built_index: dict) -> None:
    """chunks.jsonl has exactly one line per chunk."""
    lines = [
        l for l in built_index["jsonl_path"].read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    assert len(lines) == len(built_index["chunks"])


def test_chunks_jsonl_is_deterministic(tmp_path: Path) -> None:
    """Rebuilding produces byte-for-byte identical chunks.jsonl."""
    docs = inventory_documents(DOCS_DIR)
    all_chunks: list[Chunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    all_chunks = resolve_versions(docs, all_chunks)

    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    _, jsonl1 = build_index(all_chunks, out1)
    _, jsonl2 = build_index(all_chunks, out2)

    assert jsonl1.read_bytes() == jsonl2.read_bytes()


def test_build_index_raises_if_fts5_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """build_index() raises FTS5NotAvailableError when check_fts5 returns False."""
    import kb.index as index_module

    monkeypatch.setattr(index_module, "check_fts5", lambda: False)
    fake_chunk = Chunk(
        chunk_id="FAKE-01_1.0_chunk0",
        doc_id="FAKE-01",
        section="Test",
        chunk_index=0,
        content="content",
        content_hash="b" * 64,
        version="1.0",
        effective_date="2026-01",
        owner=None,
        is_current=True,
        source_path="/fake/doc.md",
    )
    with pytest.raises(FTS5NotAvailableError):
        build_index([fake_chunk], tmp_path)
