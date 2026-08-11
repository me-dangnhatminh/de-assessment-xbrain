"""##-level chunking with document header prepend and deterministic content hashing.

Each document is split at ``## `` boundaries. The document-level ``# `` heading
and the bold metadata line are prepended to every chunk so that each chunk is
self-contained with source attribution.

If a document has no ``## `` sections, the full document body (after the title
and metadata line) is returned as a single chunk.
"""

from __future__ import annotations

import hashlib
import re

from kb.models import Chunk, Document

# Matches a line starting with "## " (section heading)
_RE_SECTION_SPLIT = re.compile(r"^(## .+)$", re.MULTILINE)

# Matches the document-level title line "# ..."
_RE_TITLE = re.compile(r"^(# .+)$", re.MULTILINE)

# Matches the bold metadata line
_RE_METADATA_LINE = re.compile(r"^(\*\*.*\*\*.*)$", re.MULTILINE)


def _sha256_text(text: str) -> str:
    """Return SHA-256 hex digest of *text* encoded as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_chunk_id(doc_id: str, version: str | None, hint: str | None, index: int) -> str:
    """Build a deterministic chunk_id string."""
    version_label = version or (hint.lstrip("_") if hint else "v0")
    return f"{doc_id}_{version_label}_chunk{index}"


def chunk_document(doc: Document) -> list[Chunk]:
    """Split *doc* into ##-level chunks with prepended document header.

    Parameters
    ----------
    doc:
        A :class:`Document` instance whose ``source_path`` points to a readable file.

    Returns
    -------
    Ordered list of :class:`Chunk` objects (chunk_index is 0-based).
    """
    import pathlib

    text = pathlib.Path(doc.source_path).read_text(encoding="utf-8")

    # Extract the # title line
    title_match = _RE_TITLE.search(text)
    title_line = title_match.group(1).strip() if title_match else ""

    # Extract the bold metadata line (first ** line)
    meta_match = _RE_METADATA_LINE.search(text)
    meta_line = meta_match.group(1).strip() if meta_match else ""

    # Header to prepend to every chunk
    header = f"{title_line}\n\n{meta_line}\n\n" if meta_line else f"{title_line}\n\n"

    # Split the document body at ## boundaries
    # Find all positions of ## headings
    splits = list(_RE_SECTION_SPLIT.finditer(text))

    if not splits:
        # No ## sections: single chunk containing the full text after the header block
        # Strip the title and metadata lines from the top of the body
        body = text
        # Remove the # title line
        if title_match:
            body = body[title_match.end() :].lstrip("\n")
        # Remove the bold metadata line
        if meta_match:
            # Re-search in the stripped body
            meta_in_body = _RE_METADATA_LINE.search(body)
            if meta_in_body:
                body = body[meta_in_body.end() :].lstrip("\n")
        content = f"{header}{body}".rstrip() + "\n"
        return [
            Chunk(
                chunk_id=_build_chunk_id(doc.doc_id, doc.version, doc.filename_version_hint, 0),
                doc_id=doc.doc_id,
                section="(full document)",
                chunk_index=0,
                content=content,
                content_hash=_sha256_text(content),
                version=doc.version,
                effective_date=doc.effective_date,
                owner=doc.department,
                is_current=True,
                source_path=doc.source_path,
            )
        ]

    chunks: list[Chunk] = []
    for i, section_match in enumerate(splits):
        section_heading = section_match.group(1).strip()
        section_title = section_heading.lstrip("#").strip()

        # Body of this section: from after this heading to the start of the next
        body_start = section_match.end()
        body_end = splits[i + 1].start() if i + 1 < len(splits) else len(text)
        section_body = text[body_start:body_end].rstrip()

        content = f"{header}{section_heading}\n{section_body}".rstrip() + "\n"

        chunks.append(
            Chunk(
                chunk_id=_build_chunk_id(doc.doc_id, doc.version, doc.filename_version_hint, i),
                doc_id=doc.doc_id,
                section=section_title,
                chunk_index=i,
                content=content,
                content_hash=_sha256_text(content),
                version=doc.version,
                effective_date=doc.effective_date,
                owner=doc.department,
                is_current=True,  # overwritten later by resolve_versions()
                source_path=doc.source_path,
            )
        )

    return chunks
