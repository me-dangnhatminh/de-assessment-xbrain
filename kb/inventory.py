"""Document inventory: discover, hash, and parse metadata for all KB source documents.

Usage::

    from kb.inventory import inventory_documents
    docs = inventory_documents(Path("docs/onboard/datapack/data/docs"))

Returns a list of :class:`kb.models.Document` objects sorted by source path for
deterministic ordering across runs.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from kb.metadata import parse_metadata_line
from kb.models import Document

# Parses "POL-01" from "POL-01_chinh_sach_backup_v2.md"
_RE_DOC_ID = re.compile(r"^([A-Z]+-\d+)")

# Parses "_v1" or "_v2" from the stem
_RE_VERSION_HINT = re.compile(r"(_v\d+)$", re.IGNORECASE)

# The bold metadata line is the first line that starts with "**"
_RE_METADATA_LINE = re.compile(r"^\*\*.*\*\*", re.MULTILINE)


def _sha256_file(path: Path) -> str:
    """Return SHA-256 hex digest of a file without modifying it."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _extract_metadata_line(text: str) -> str | None:
    """Return the first bold metadata line from a document's text, or None."""
    match = _RE_METADATA_LINE.search(text)
    if match:
        return match.group(0).strip()
    return None


def inventory_documents(docs_dir: Path) -> list[Document]:
    """Discover and inventory all Markdown documents in *docs_dir*.

    Parameters
    ----------
    docs_dir:
        Path to the directory containing the operational Markdown files.
        Must exist.

    Returns
    -------
    Sorted list of :class:`Document` objects, one per ``.md`` file found.

    Raises
    ------
    FileNotFoundError
        When *docs_dir* does not exist.
    """
    docs_dir = Path(docs_dir).expanduser().resolve()
    if not docs_dir.exists():
        raise FileNotFoundError(f"docs directory does not exist: {docs_dir}")
    if not docs_dir.is_dir():
        raise FileNotFoundError(f"docs path is not a directory: {docs_dir}")

    md_files = sorted(docs_dir.glob("*.md"))
    documents: list[Document] = []

    for path in md_files:
        stem = path.stem  # e.g. "POL-01_chinh_sach_backup_v2"

        # Parse doc_id from prefix
        doc_id_match = _RE_DOC_ID.match(stem)
        doc_id = doc_id_match.group(1) if doc_id_match else stem

        # Parse filename version hint
        hint_match = _RE_VERSION_HINT.search(stem)
        filename_version_hint = hint_match.group(1).lower() if hint_match else None

        # Hash the file
        sha256 = _sha256_file(path)

        # Read content and extract metadata
        text = path.read_text(encoding="utf-8")
        meta_line = _extract_metadata_line(text)
        if meta_line:
            meta = parse_metadata_line(meta_line)
        else:
            meta = {
                "version": None,
                "effective_date": None,
                "department": None,
                "approver": None,
                "supersedes_previous": False,
            }

        documents.append(
            Document(
                source_path=str(path),
                doc_id=doc_id,
                filename_version_hint=filename_version_hint,
                sha256=sha256,
                version=meta["version"],
                effective_date=meta["effective_date"],
                department=meta["department"],
                approver=meta["approver"],
                supersedes_previous=meta["supersedes_previous"],
            )
        )

    return documents
