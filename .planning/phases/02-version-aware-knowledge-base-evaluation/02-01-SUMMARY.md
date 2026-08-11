---
plan: 02-01
phase: 02-version-aware-knowledge-base-evaluation
status: complete
completed: 2026-08-12
commits:
  - d54802e  feat(02-01): Task 1 — inventory, metadata, and chunking pipeline
  - e8308ca  feat(02-01): Task 2 — version resolution and SQLite FTS5 index build
  - f24af2d  feat(02-01): Task 3 — FTS5 search functions and Makefile targets
---

# Plan 02-01 Summary — KB Pipeline: Inventory, Index, Search

## What Was Built

A complete `kb/` Python package implementing the version-aware knowledge base
pipeline for all 8 supplied Vietnamese operational documents.

### Task 1 — Inventory, Metadata Extraction, and Chunking

**Files:** `kb/__init__.py`, `kb/__main__.py`, `kb/models.py`, `kb/inventory.py`,
`kb/metadata.py`, `kb/chunking.py`, `tests/kb/test_inventory.py`,
`tests/kb/test_metadata.py`, `tests/kb/test_chunking.py`

- `Document` and `Chunk` dataclasses in `kb/models.py` establish the typed
  contract for the entire pipeline.
- `inventory_documents()` globs the docs directory, parses `doc_id` from the
  filename prefix (e.g. `POL-01`), extracts `_v1`/`_v2` hints, computes
  SHA-256 per file, and extracts metadata from each bold header line.
- `parse_metadata_line()` handles all 8 document patterns via regex:
  `Phiên bản X.Y` → version, `Ban hành: MM/YYYY` / `Cập nhật: MM/YYYY` →
  effective_date (YYYY-MM), `Người duyệt:` → approver, `Thay thế phiên bản trước`
  → supersedes_previous flag. Uses `\S+` in the Vietnamese keyword patterns to
  handle Unicode NFC/NFD normalization differences in precomposed characters.
- `chunk_document()` splits at `## ` boundaries, prepends the `# ` title and
  bold metadata line to every chunk (D-06), and computes SHA-256 of the final
  chunk text. Documents with no `## ` sections produce a single full-body chunk.
- **Bug discovered and fixed:** `_extract_metadata_line` regex originally stopped
  at the closing `**`, truncating ` · Cập nhật: 07/2026`. Fixed to `^\*\*[^\n]*$`.
- 45 tests, all passing.

### Task 2 — Version Resolution and SQLite FTS5 Index

**Files:** `kb/versioning.py`, `kb/index.py`, `tests/kb/test_versioning.py`,
`tests/kb/test_index.py`

- `resolve_versions()` groups documents by `doc_id`. For multi-version families,
  checks `supersedes_previous` first (D-08); falls back to `effective_date`
  lexicographic comparison (D-07). Sole-version documents are always current.
- `check_fts5()` probes FTS5 availability; `build_index()` raises
  `FTS5NotAvailableError` if unavailable.
- `build_index()` creates `chunks_meta` (normal table, all chunk fields) and
  `chunks_fts` (FTS5 virtual table, `content_rowid=rowid`). Inserts all chunks
  with parameterized queries, then writes deterministic `chunks.jsonl` sorted by
  `(doc_id, version, chunk_index)`.
- POL-01 v2 correctly marked `is_current=1`; v1 marked `is_current=0`.
- 22 tests, all passing.

### Task 3 — FTS5 Search and Makefile Targets

**Files:** `kb/search.py`, `tests/kb/test_search.py`, `Makefile`

- `search_current()` filters `WHERE is_current=1` before BM25 ranking.
- `search_all()` omits the filter for all-versions historical inspection.
- Both use `?` parameter binding exclusively — no string interpolation in SQL
  (T-02-01 mitigated). `_safe_fts_query()` phrase-wraps input in double-quotes
  to handle punctuation without FTS5 syntax errors; returns `[]` on empty input.
- Makefile: `kb-build` and `kb-search` targets added with `KB_OUTPUT_DIR` variable.
- 17 tests, all passing.

## Evidence

End-to-end build succeeded:
```
build complete: 8 documents, 22 chunks (20 current, 2 superseded)
  index: data/evidence/phase2/index.sqlite
  chunks: data/evidence/phase2/chunks.jsonl
```

Current-policy search for "sao lưu":
```
Results for 'sao lưu' — current versions only (top 2)
1. POL-01 v2.0 2026-05 [CURRENT] § Quy định    bm25: -2.2292
2. POL-01 v2.0 2026-05 [CURRENT] § Trách nhiệm  bm25: -2.1280
```
POL-01 v1 (superseded) is excluded from current-mode results.

Source documents verified unchanged: `git diff --exit-code -- docs/onboard` passes.

## Test Results

| Suite | Tests | Result |
|---|---|---|
| tests/kb/test_inventory.py | 10 | PASS |
| tests/kb/test_metadata.py | 22 | PASS |
| tests/kb/test_chunking.py | 13 | PASS |
| tests/kb/test_versioning.py | 7 | PASS |
| tests/kb/test_index.py | 15 | PASS |
| tests/kb/test_search.py | 17 | PASS |
| **Total** | **84** | **PASS** |

`uv run ruff check kb/ tests/kb/` — clean
`uv run ruff format --check kb/ tests/kb/` — clean

## Decisions Recorded

- Unicode NFC/NFD: Vietnamese precomposed chars differ between test string
  literals (NFC) and file bytes. Fixed with `\S+` in keyword positions
  rather than explicit character classes.
- Metadata line regex: must capture the full line (`[^\n]*`) not just the
  bold-delimited portion, because fields follow after the closing `**`.
- Test fixtures for versioning: must use distinct `source_path` per document
  because `resolve_versions` keys on path to match chunks to their winner.
- FTS5 phrase-quoting: user queries wrapped in double-quotes for safe handling
  of punctuation and multi-word Vietnamese phrases.
- "backup" has no FTS5 match in Vietnamese docs (the word is "sao lưu");
  test updated to use Vietnamese vocabulary.

## Constraints Respected

- No files under `docs/onboard/datapack/` modified.
- No new Python dependencies added (stdlib sqlite3 only).
- No embedding/vector search, LLM calls, or external services.
- Vietnamese source content indexed as-is; not translated.
