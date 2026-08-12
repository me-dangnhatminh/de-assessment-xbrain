---
phase: 02-version-aware-knowledge-base-evaluation
reviewed: 2026-08-12T07:20:18Z
depth: standard
files_reviewed: 22
files_reviewed_list:
  - kb/__init__.py
  - kb/__main__.py
  - kb/models.py
  - kb/inventory.py
  - kb/metadata.py
  - kb/chunking.py
  - kb/versioning.py
  - kb/index.py
  - kb/search.py
  - kb/eval_cases.py
  - kb/eval_runner.py
  - kb/eval_report.py
  - tests/kb/test_inventory.py
  - tests/kb/test_metadata.py
  - tests/kb/test_chunking.py
  - tests/kb/test_versioning.py
  - tests/kb/test_index.py
  - tests/kb/test_search.py
  - tests/kb/test_eval_cases.py
  - tests/kb/test_eval_runner.py
  - Makefile
  - sop/kb_update_sop.md
findings:
  critical: 0
  warning: 6
  info: 7
  total: 13
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-08-12T07:20:18Z
**Depth:** standard
**Files Reviewed:** 22
**Status:** issues_found

## Summary

Reviewed the full Phase 02 pipeline (`kb/` package, 8 test files, Makefile, SOP) for the version-aware knowledge base. The core data flow is sound: parameterized FTS5 queries (no SQL injection — verified with live injection attempts against a real index), deterministic chunking/hashing, correct `is_current` resolution for the actual POL-01 v1/v2 supersession data, deterministic `chunks.jsonl` export (byte-identical rebuild test passes), and an accurate one-page SOP (569 words, commands match the CLI). The full test suite passes (108/108) and `ruff check`/`format` are clean.

The defects found are in the robustness and *acceptance-evidence* layers rather than the happy-path data:

1. The eval scorer cannot detect a wrong-version retrieval for the version-trap cases (Q08/Q09) — the flagship cases can report `pass` while retrieving only the superseded v1 policy.
2. A failed `kb build` destroys the previously-good index and leaves `index.sqlite`/`chunks.jsonl` mutually inconsistent (reproduced by fault injection).
3. `_write_atomic()` double-closes a file descriptor on failure, masking the real error and leaking the temp file (reproduced).
4. `kb search` against a non-SQLite file crashes with an unhandled `sqlite3.DatabaseError` traceback (reproduced).

No BLOCKERs: the produced data and evidence for the current documents are correct; all issues are latent defects, robustness gaps, or maintainability traps.

## Warnings

### WR-01: Version-trap scoring cannot detect retrieval of the wrong (superseded) version

**File:** `kb/eval_runner.py:107-120`
**Issue:** `score_retrieval_hit()` matches expected sources only by `(doc_id, section)` and ignores `is_current`. The declared `pass_criteria` for the flagship version-trap cases are not enforced by the score:
- Q08 (`kb/eval_cases.py:210-213`) declares *"POL-01 v1 must NOT be the top result"* — but `score_retrieval_hit(Q08, [POL-01 v1 "Quy định", is_current=False])` returns `pass` (verified by direct call).
- Q09 (`kb/eval_cases.py:233-236`) declares *"top-k contains POL-01 v1 AND POL-01 v2 chunks"* — but a result set containing only the superseded v1 also returns `pass`.

The v1-vs-v2 check exists only as an advisory line in `_build_diagnosis()` (lines 225-252); it never affects the verdict. A regression in `resolve_versions()` (e.g. v1 wrongly marked current) would therefore be reported as `PASS` in the committed `eval_results.json` — the exact failure this evaluation exists to catch.
**Fix:** In `score_retrieval_hit()` (or in `run_evaluation`), special-case `question_type == "version_trap"` and require `is_current` evidence: for `search_mode == "current"`, the matching POL-01 chunk must have `is_current is True`; for `search_mode == "all"` (Q09), require at least one POL-01 chunk with `is_current True` AND at least one with `is_current False`. Downgrade the verdict to `fail`/`partial` when those constraints fail.

### WR-02: A failed `kb build` destroys the previous index and leaves index.sqlite/chunks.jsonl inconsistent

**File:** `kb/index.py:133-175`
**Issue:** `db_path.unlink()` runs *before* the new database is built (lines 134-135). Any exception between the unlink and `conn.commit()` leaves the previous good index destroyed and a new, partially-built (or empty) `index.sqlite` on disk, while `chunks.jsonl` still holds the old, now-stale content. Reproduced by fault injection into the FTS insert: the pre-existing 28,672-byte index became an empty 8,192-byte DB with 0 rows, and the old `chunks.jsonl` remained untouched. For a pipeline whose stated core value is regenerable, source-grounded evidence, a failed rebuild silently orphaning the evidence pair is a data-integrity hazard.
**Fix:** Build into a temporary DB file (e.g. `index.sqlite.tmp-<pid>` in the output dir), then `os.replace()` it over `index.sqlite` only after the commit succeeds; write `chunks.jsonl` only after both succeed (mirroring `_write_atomic`). Optionally delete stale `-wal`/`-shm` sidecar files after `os.replace`.

### WR-03: `_write_atomic()` double-closes the fd on failure, masking the real error and leaking the temp file

**File:** `kb/index.py:83-97`
**Issue:** In the `except` branch, `os.close(fd)` is called unconditionally. If the failure happens after `os.close(fd)` succeeded in the `try` (i.e. `os.replace` raises), the second `os.close(fd)` raises `OSError: [Errno 9] Bad file descriptor`, which replaces the original exception, and `os.unlink(tmp_name)` is never reached so the temp file leaks. Reproduced: patching `os.replace` to raise `PermissionError` surfaced `OSError [Errno 9]` to the caller and left `tmpkrkpdt11` in the directory.
**Fix:** Track closure state, e.g. `closed = False` → `os.write(fd, content); os.close(fd); closed = True; os.replace(...)`, and in the `except` only `os.close(fd)` when `not closed`. Use `try/finally` for the unlink.

### WR-04: `search_current()`/`search_all()` crash with an unhandled `sqlite3.DatabaseError` and leak the connection on the error path

**File:** `kb/search.py:133-173`
**Issue:** Both functions catch only `sqlite3.OperationalError`. Passing a non-SQLite file (or a corrupt DB) raises `sqlite3.DatabaseError: file is not a database`, which propagates as a raw traceback — reproduced via `python -m kb search --db /tmp/bad.sqlite`. The CLI's pre-check (`kb/__main__.py:86-88`) only verifies the file exists, so a corrupt/wrong file reaches the crash. Additionally, on the `OperationalError` path `conn` is never closed, and `sqlite3.connect()` silently *creates* an empty DB file if the path doesn't exist (see IN-02).
**Fix:** Catch `sqlite3.DatabaseError` alongside `OperationalError` (return `[]`), and close the connection in a `finally` block, e.g. `conn = sqlite3.connect(db_path); try: rows = conn.execute(...).fetchall() finally: conn.close()`.

### WR-05: Duplicate, conflicting `EvalCase`/`EvalResult` definitions — dead code in `kb/models.py`

**File:** `kb/models.py:126-147`
**Issue:** `models.py` defines `EvalCase` and `EvalResult` with a *different* interface than the ones actually used (`kb/eval_cases.py:28` and `kb/eval_runner.py:36`): e.g. `models.EvalResult` has `retrieval_hit`/`groundedness_diagnosis`/`overall_score`/`notes`, while the live object has `retrieval_hit_score`/`groundedness_score`/`diagnosis` (no `overall_score`, no `notes`). Nothing imports the `models.py` versions (verified by grep), so the module docstrings are actively misleading for anyone reading `kb/models.py` to understand the eval contract.
**Fix:** Delete the `EvalCase`/`EvalResult` dataclasses from `kb/models.py` (keep `Document`/`Chunk`/`SearchResult`), or make the eval modules import from `kb.models` so there is a single definition.

### WR-06: Metadata parser's claimed Unicode-normalization handling fails on NFD-decomposed text

**File:** `kb/metadata.py:23-29` (patterns), `68-70` (version extraction)
**Issue:** The comment at lines 27-29 says the patterns handle "Unicode normalization differences," but the character classes `[eê]` and `[aả]` match only the precomposed forms. For an NFD-decomposed metadata line (common when a file is edited on macOS or pasted from decomposed sources), `Phiên bản` becomes `Phie^n ba^'n` and the version regex fails. Verified: `parse_metadata_line(unicodedata.normalize("NFD", line))` returns `version=None` (the date regex still matched via `\S+`). The shipped docs are NFC (verified), so this is latent, but the module's documented guarantee is false.
**Fix:** Normalize at entry: `line = unicodedata.normalize("NFC", line)` as the first statement of `parse_metadata_line()`. Cheap, deterministic, and makes the claim true.

## Info

### IN-01: Negative `--top-k` silently returns all rows

**File:** `kb/__main__.py:184` (also `:202`), `kb/search.py:46,64`
**Issue:** `--top-k -1` is accepted and SQLite `LIMIT -1` means "no limit," so the CLI prints every matching chunk. `--top-k 0` returns nothing. No validation.
**Fix:** Add `type=int` validation in argparse, e.g. a custom type that rejects values `< 1`.

### IN-02: Search functions create an empty SQLite file at a non-existent db_path

**File:** `kb/search.py:137,168`
**Issue:** `sqlite3.connect(db_path)` creates an empty DB when the file doesn't exist (reproduced: `search_all("/tmp/.../nonexistent.sqlite", "x")` left a 0-byte `.sqlite` file). A typo'd path now "exists," which can mask later CLI calls that only check `db_path.is_file()`.
**Fix:** Check `db_path.is_file()` and return `[]` (or raise a clear error) before connecting, or open with `sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)`.

### IN-03: `chunk_id` collision if two family docs declare the same metadata version

**File:** `kb/chunking.py:33-36`
**Issue:** `_build_chunk_id()` prefers the parsed `version` over the filename hint. If `POL-01_v1.md` declared `Phiên bản 2.0` in its metadata (a copy-paste error), its chunks would collide with the genuine v2 chunks (`POL-01_2.0_chunk0`), silently overwriting rows in the index (chunk_id is not a UNIQUE column).
**Fix:** Include the filename hint in the key, e.g. `f"{doc_id}_{version_label}_{hint or 'v0'}_chunk{index}"`, and/or add `UNIQUE(chunk_id)` to `chunks_meta` to fail loudly.

### IN-04: Eval integration tests silently skip when the committed index is absent

**File:** `tests/kb/test_eval_runner.py:13-15`, `tests/kb/test_eval_cases.py:163-165,180-182`
**Issue:** Seven integration tests `@SKIP_NO_INDEX` skip whenever `data/evidence/phase2/index.sqlite` is missing. On a fresh checkout, `make verify-phase1`'s `pytest -q` would silently skip the entire eval-integration coverage rather than fail, so a regression in `run_evaluation` could go unnoticed.
**Fix:** Build the index in a fixture (as `test_search.py` does with `tmp_path_factory`) instead of depending on the committed artifact; drop the skip markers.

### IN-05: `make phase2` rebuilds the index twice

**File:** `Makefile:69-74`
**Issue:** `phase2: kb-build kb-eval`, and `kb-eval` depends on `$(KB_OUTPUT_DIR)/index.sqlite` → `kb-build` (line 69). Because `kb-build` is `.PHONY`, it always runs again, so `make phase2` builds the index twice (and runs `uv sync --locked` twice).
**Fix:** Make `phase2` depend only on `kb-eval` (`phase2: kb-eval`), which already rebuilds via its dependency chain.

### IN-06: `effective_date` uses the older `Ban hành` date when a line contains both `Ban hành` and `Cập nhật`

**File:** `kb/metadata.py:72-77`
**Issue:** `_RE_DATE.search()` returns the first match. A header containing both `Ban hành: 01/2025 · Cập nhật: 02/2026` yields `2025-01` (verified) — the issue date, not the latest update date that a version-aware KB would want for `is_current` fallback.
**Fix:** Prefer `Cập nhật` over `Ban hành` when both are present (search for the update pattern first).

### IN-07: No-date, no-supersession families pick the alphabetically-first file as current

**File:** `kb/versioning.py:22-24,65-68`
**Issue:** When a family has multiple docs with `effective_date=None` and no supersession phrase, `max(members, key=_effective_date_key)` with the `"0000-00"` sentinel returns the first document in input order, which (per `inventory_documents`) is alphabetical — so `..._v1.md` would win over `..._v2.md`. Deterministic, but likely the wrong semantic choice for a multi-file family that lacks explicit dates.
**Fix:** In the no-date fallback, prefer the highest filename version hint (`_v\d+`) instead of input order.

---

_Reviewed: 2026-08-12T07:20:18Z_
_Reviewer: Claude (gsd-code-reviewer via generic-agent workaround)_
_Depth: standard_
