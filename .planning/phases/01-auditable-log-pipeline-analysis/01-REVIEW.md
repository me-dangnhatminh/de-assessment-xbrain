---
phase: 01-auditable-log-pipeline-analysis
reviewed: 2026-08-11T12:28:36Z
depth: standard
files_reviewed: 35
files_reviewed_list:
  - pyproject.toml
  - uv.lock
  - pipeline/__main__.py
  - pipeline/models.py
  - pipeline/ingest.py
  - pipeline/validation.py
  - pipeline/integrity.py
  - pipeline/normalize.py
  - pipeline/write_outputs.py
  - pipeline/analysis.py
  - pipeline/manifest.py
  - pipeline/report.py
  - pipeline/sql/00_tracer_service_error_counts.sql
  - pipeline/sql/01_service_error_counts.sql
  - pipeline/sql/02_daily_error_counts.sql
  - pipeline/sql/03_top_normalized_errors.sql
  - pipeline/sql/04_quality_reconciliation.sql
  - tests/pipeline/test_tracer.py
  - tests/pipeline/test_validation.py
  - tests/pipeline/test_pipeline_outputs.py
  - tests/pipeline/test_analysis.py
  - tests/pipeline/test_evidence.py
  - tests/pipeline/test_end_to_end.py
  - Makefile
  - README.md
  - .gitignore
  - data/evidence/phase1/source_manifest.json
  - data/evidence/phase1/quality_ledger.jsonl
  - data/evidence/phase1/schema.json
  - data/evidence/phase1/tables/01_service_error_counts.csv
  - data/evidence/phase1/tables/02_daily_error_counts.csv
  - data/evidence/phase1/tables/03_top_normalized_errors.csv
  - data/evidence/phase1/tables/04_quality_reconciliation.csv
  - data/evidence/phase1/report.md
  - data/evidence/phase1/run_manifest.json
findings:
  critical: 2
  warning: 5
  info: 0
  total: 7
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-08-11T12:28:36Z
**Depth:** standard
**Files Reviewed:** 35
**Status:** issues_found

## Summary

The current committed evidence reconstructs from the canonical source and lint passes, but the production trust boundary is not safe to ship. A symlink below an otherwise approved output root can modify immutable inputs, and `verify` can certify a fully replaced, internally consistent set of output artifacts without proving they were derived from those inputs. The remaining findings concern ledger correctness, standards-compliant parsing, trace fidelity, and test isolation.

## Critical Issues

### CR-01: Descendant symlinks bypass the immutable-source output guard [BLOCKER]

**File:** `pipeline/integrity.py:56`

**Issue:** `validate_output_root()` resolves and checks only the root. It does not constrain the descendants subsequently used by `cmd_run()` (for example, `evidence/phase1/quality_ledger.jsonl` at `pipeline/__main__.py:473`) or by cleanup (`pipeline/__main__.py:441`). An attacker or stale workspace can create `OUTPUT_ROOT/evidence -> docs/onboard` or `OUTPUT_ROOT/processed -> docs/onboard/...`. `mkdir()` and the atomic writers then follow that descendant symlink and replace a supplied file; `all --clean` can unlink one. The inventory comparison happens only after writes, so it detects the change after immutable input has already been damaged.

**Fix:** Resolve and authorize every final artifact path before opening, replacing, or unlinking it. Reject a target unless its resolved path is contained by the resolved output root and outside `SUPPLIED_ROOT`; also reject symlinked ancestor directories (or use directory file descriptors with `O_NOFOLLOW`). Apply the same helper to cleanup targets. Add regression tests for `evidence` and `processed` descendant symlinks pointing into `docs/onboard` and assert no supplied file is created, changed, or removed.

### CR-02: Manifest verification does not prove generated evidence came from the canonical input [BLOCKER]

**File:** `pipeline/manifest.py:302`

**Issue:** `_verify_row_counts()` derives only final-action totals from the JSONL ledger and the number of Parquet rows. It never validates ledger source lines, raw records, digests, issue decisions, normalizations, or Parquet rows against the live canonical log. An attacker can replace the ledger and Parquet with fabricated data that preserves the five counts, regenerate all CSVs and the manifest with `build_run_manifest()`, and receive `run manifest verified`. The final `run_id` check at `pipeline/manifest.py:417` is self-referential: it hashes the current artifacts, so a regenerated forged artifact set gets a matching ID. This contradicts the submission's source-grounded and fail-closed verification claim.

**Fix:** In verification, deterministically re-run validation/normalization from `CANONICAL_LOG_INPUT` into a temporary, non-symlinked location (or independently derive and compare a signed/committed canonical ledger-and-Parquet digest) and compare the live ledger, Parquet, analyses, and all conservation fields to that reconstruction. At minimum, strictly validate each ledger entry's complete schema, contiguous source line, source hash/path, digest, and action before comparing it to re-derived entries. Add a test that changes a ledger `raw_line` or Parquet value without changing row counts, rebuilds the manifest, and expects verification to fail.

## Warnings

### WR-01: Duplicate provenance falsely calls rejected records “retained” [WARNING]

**File:** `pipeline/__main__.py:361`

**Issue:** Both validation paths insert every parsed record digest into `first_source_line_by_digest` before deciding its `final_action` (also `pipeline/__main__.py:309`). If the first copy is invalid and rejected, a later copy is labelled `EXACT_DUPLICATE` with `retained_source_line` set to that rejected line, despite the policy saying it “was first retained.” This makes the audit ledger's duplicate provenance false.

**Fix:** Determine the first record's action before recording it as retained, and add it to the digest map only for `ACCEPT`/`REPAIR` records (or rename the field and policy consistently to “first observed”). Add a test with two identical invalid records.

### WR-02: UTF-8 validity check rejects valid replacement-character data [WARNING]

**File:** `pipeline/ingest.py:52`

**Issue:** Input is decoded with `errors="replace"`, then any U+FFFD character is treated as proof of invalid UTF-8 at line 62. U+FFFD is a valid Unicode code point and can legitimately occur in a valid JSON string, so valid log rows are rejected and their raw provenance is altered.

**Fix:** Decode with strict UTF-8 in a `try`/`except UnicodeDecodeError`; create `TEXT_INVALID_UTF8` only on that exception. Preserve a byte-safe representation for invalid rows if raw provenance is required. Add a valid JSON record containing `"\uFFFD"` and assert that it is accepted.

### WR-03: JSONL parsing accepts non-standard JSON constants [WARNING]

**File:** `pipeline/ingest.py:83`

**Issue:** Python's default `json.loads()` accepts `NaN`, `Infinity`, and `-Infinity`. A record containing one in an unexpected field passes validation as `UNEXPECTED_FIELD`/`ACCEPT`; the later default `json.dumps()` can emit the same non-standard token into the ledger. That violates the JSONL evidence contract and makes downstream parsing dependent on permissive parsers.

**Fix:** Supply a `parse_constant` callback that raises `ValueError` to every evidence/source JSON parse, converting it into a rejecting `JSON_MALFORMED` issue. Use `allow_nan=False` for all evidence serialization. Add malformed-constant tests for source records and ledger verification.

### WR-04: `trace` implements different validation and normalization rules than the production pipeline [WARNING]

**File:** `pipeline/__main__.py:125`

**Issue:** `parse_and_normalize()` does not call `validate_record()` or `normalize_error()`. For example, it accepts any non-empty level, stores raw `SMTPConnRefused` rather than the production `SMTP_CONN_REFUSED` taxonomy, hashes raw JSON text instead of the canonical record object, emits lowercase `"accept"`, and produces a different normalizations schema. The command advertises a trace through “every Phase 1 evidence seam,” but its artifacts cannot be compared to the production ledger or Parquet contract.

**Fix:** Reuse the validation, duplicate/disposition (where applicable), normalization, `CleanRecord`, and `LedgerEntry` functions used by `_run_validation_stream()`. Either produce the same schema and values or clearly isolate trace as a diagnostic format with a separate contract. Test a traced canonical line against the corresponding full-run ledger/Parquet row.

### WR-05: A test mutates a tracked production SQL file in the shared working tree [WARNING]

**File:** `tests/pipeline/test_evidence.py:274`

**Issue:** The tamper test appends to `pipeline/sql/01_service_error_counts.sql` and restores it in `finally`. This makes tests unsafe alongside another test process, reviewer command, editor save, or interruption that prevents restoration; it can also make unrelated manifest verification flaky. Test reliability is part of the evidence boundary here.

**Fix:** Copy the SQL fixture into a temporary repository root/output fixture and monkeypatch the module's repository-root/path dependency, or test a temporary generated artifact only. Never write a tracked source file from a test.

---

_Reviewed: 2026-08-11T12:28:36Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
