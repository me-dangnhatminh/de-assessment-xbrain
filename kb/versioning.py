"""Deterministic is_current resolution across doc_id families.

Algorithm (Decision D-07 and D-08):
1. Group chunks by doc_id.
2. For each group with multiple documents:
   a. If any document in the family has ``supersedes_previous=True``, that
      document is current; all others are superseded.
   b. If no supersession phrase is present, compare ``effective_date`` strings
      (ISO ``YYYY-MM`` lexicographic order). The latest date wins; ties keep the
      first encountered document (deterministic input order).
3. Solo-version families are always current.

Returns a new list of :class:`Chunk` objects (immutable dataclasses replaced
with updated ``is_current`` values).
"""

from __future__ import annotations

from kb.models import Chunk, Document


def _effective_date_key(doc: Document) -> str:
    """Return a sortable key for effective_date; missing dates sort earliest."""
    return doc.effective_date or "0000-00"


def resolve_versions(documents: list[Document], chunks: list[Chunk]) -> list[Chunk]:
    """Set ``is_current`` on each chunk based on version precedence within its doc_id family.

    Parameters
    ----------
    documents:
        All inventoried documents.  Used to determine which versions exist per
        doc_id and which carries the supersession phrase.
    chunks:
        All chunks produced by :func:`kb.chunking.chunk_document`.  Their
        ``is_current`` values are overwritten by this function.

    Returns
    -------
    A new list of :class:`Chunk` objects with ``is_current`` set correctly.
    The order matches the input *chunks* list.
    """
    # Build a mapping: doc_id → list of documents (preserves input order)
    family: dict[str, list[Document]] = {}
    for doc in documents:
        family.setdefault(doc.doc_id, []).append(doc)

    # Determine current source_path per doc_id family
    current_paths: set[str] = set()

    for members in family.values():
        if len(members) == 1:
            # Sole version — always current
            current_paths.add(members[0].source_path)
            continue

        # Check for explicit supersession phrase first (D-08)
        superseding = [m for m in members if m.supersedes_previous]
        if superseding:
            # The document(s) carrying the supersession phrase are current.
            # If multiple carry it, pick the one with the latest effective_date.
            winner = max(superseding, key=_effective_date_key)
            current_paths.add(winner.source_path)
        else:
            # Fallback: latest effective_date wins (D-07)
            winner = max(members, key=_effective_date_key)
            current_paths.add(winner.source_path)

    # Rewrite chunks with the resolved is_current flag
    updated: list[Chunk] = []
    for chunk in chunks:
        is_current = chunk.source_path in current_paths
        if is_current != chunk.is_current:
            # Replace immutable dataclass with updated value
            chunk = Chunk(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                section=chunk.section,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                content_hash=chunk.content_hash,
                version=chunk.version,
                effective_date=chunk.effective_date,
                owner=chunk.owner,
                is_current=is_current,
                source_path=chunk.source_path,
            )
        updated.append(chunk)

    return updated
