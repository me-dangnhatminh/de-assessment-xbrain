"""SQLite FTS5 index creation, chunk insertion, and chunks.jsonl canonical export.

Schema
------
``chunks_meta`` — normal table holding all chunk columns plus a ``status`` column
(always ``"active"`` for now; reserved for future soft-delete).

``chunks_fts`` — FTS5 virtual table over the ``content`` column using
``content_rowid`` pointing to ``chunks_meta.rowid`` so that the full-text index
shares storage with the metadata table.

Output
------
- ``<output_dir>/index.sqlite``  — rebuildable SQLite database
- ``<output_dir>/chunks.jsonl``  — deterministic line-delimited JSON export
  sorted by (doc_id, version, chunk_index)
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path

from kb.models import Chunk

# Schema DDL
_DDL_CHUNKS_META = """
CREATE TABLE IF NOT EXISTS chunks_meta (
    chunk_id      TEXT NOT NULL,
    doc_id        TEXT NOT NULL,
    section       TEXT NOT NULL,
    version       TEXT,
    effective_date TEXT,
    owner         TEXT,
    status        TEXT NOT NULL DEFAULT 'active',
    content_hash  TEXT NOT NULL,
    is_current    INTEGER NOT NULL,
    source_path   TEXT NOT NULL,
    chunk_index   INTEGER NOT NULL,
    content       TEXT NOT NULL
)
"""

_DDL_CHUNKS_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
USING fts5(content, content_rowid=rowid, tokenize='unicode61')
"""

# Sorted field order for deterministic JSONL export
_JSONL_FIELDS = (
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
)


class FTS5NotAvailableError(RuntimeError):
    """Raised when the SQLite build on this machine does not include FTS5."""


def check_fts5() -> bool:
    """Return True if SQLite FTS5 is compiled into the Python sqlite3 module."""
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE _fts5_probe USING fts5(x)")
        conn.close()
        return True
    except sqlite3.OperationalError:
        return False


def _write_atomic(path: Path, content: bytes) -> None:
    """Atomically write *content* to *path* via a sibling temp file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent)
    try:
        os.write(fd, content)
        os.close(fd)
        os.replace(tmp_name, path)
    except Exception:
        os.close(fd)
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def build_index(chunks: list[Chunk], output_dir: Path) -> tuple[Path, Path]:
    """Build the FTS5 index and write chunks.jsonl from *chunks*.

    Parameters
    ----------
    chunks:
        Version-resolved list of :class:`Chunk` objects (``is_current`` already set).
    output_dir:
        Directory where ``index.sqlite`` and ``chunks.jsonl`` will be written.
        Created if absent.

    Returns
    -------
    ``(db_path, jsonl_path)`` — absolute paths to the two output files.

    Raises
    ------
    FTS5NotAvailableError
        When FTS5 is not compiled into the sqlite3 module on this machine.
    """
    if not check_fts5():
        raise FTS5NotAvailableError(
            "SQLite FTS5 is not available on this Python build. "
            "Install a Python distribution that includes FTS5 (CPython standard builds do)."
        )

    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    db_path = output_dir / "index.sqlite"
    jsonl_path = output_dir / "chunks.jsonl"

    # --- Build SQLite index ---
    # Remove stale database to guarantee a clean rebuild
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(_DDL_CHUNKS_META)
        conn.execute(_DDL_CHUNKS_FTS)

        insert_meta = """
            INSERT INTO chunks_meta
                (chunk_id, doc_id, section, version, effective_date, owner, status,
                 content_hash, is_current, source_path, chunk_index, content)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
        """
        insert_fts = """
            INSERT INTO chunks_fts(rowid, content)
            VALUES (last_insert_rowid(), ?)
        """

        for chunk in chunks:
            conn.execute(
                insert_meta,
                (
                    chunk.chunk_id,
                    chunk.doc_id,
                    chunk.section,
                    chunk.version,
                    chunk.effective_date,
                    chunk.owner,
                    chunk.content_hash,
                    1 if chunk.is_current else 0,
                    chunk.source_path,
                    chunk.chunk_index,
                    chunk.content,
                ),
            )
            conn.execute(insert_fts, (chunk.content,))

        conn.commit()
    finally:
        conn.close()

    # --- Write deterministic chunks.jsonl ---
    # Sort by (doc_id, version-or-empty, chunk_index) for stable output
    sorted_chunks = sorted(
        chunks,
        key=lambda c: (c.doc_id, c.version or "", c.chunk_index),
    )

    lines = []
    for chunk in sorted_chunks:
        record = {field: getattr(chunk, field) for field in _JSONL_FIELDS}
        # Serialize is_current as int 0/1 for JSON readability
        record["is_current"] = 1 if chunk.is_current else 0
        lines.append(json.dumps(record, ensure_ascii=False))

    jsonl_bytes = ("\n".join(lines) + "\n").encode("utf-8")
    _write_atomic(jsonl_path, jsonl_bytes)

    return db_path, jsonl_path
