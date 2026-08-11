---
phase: 01-auditable-log-pipeline-analysis
reviewed: 2026-08-11T05:18:16Z
depth: standard
files_reviewed: 23
files_reviewed_list:
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
findings:
  critical: 2
  warning: 2
  info: 0
  total: 4
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-08-11T05:18:16Z
**Depth:** standard
**Files Reviewed:** 23
**Status:** issues_found

## Summary

The pipeline and the new live supplied-tree comparison were reviewed in context with all
registered SQL, tests, and the Phase 1 evidence contract. The three-way inventory comparison
correctly detects a forged persisted inventory, but the verifier still accepts evidence derived
from an arbitrary `--input` outside that inventory and trusts a self-declared Parquet row count.
Those gaps allow a successful verification result to make unsupported source/row-count claims.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01 [BLOCKER]: Verified manifest is not bound to the input file that produced it

**File:** `pipeline/__main__.py:456-485`; `pipeline/manifest.py:168-185,245-265`

**Issue:** `cmd_run()` processes any repository-relative path supplied to `--input`, while its
before/after inventory always hashes the fixed `docs/onboard/` tree. It records the arbitrary
path and hash in `source_manifest.json["input"]`, but `verify_run_manifest()` never validates that
field or establishes that the processed input is a supplied file. An attacker can place a valid
JSONL file elsewhere in the repository, run the normal stages with that file, and obtain a passing
`verify` result: the live `docs/onboard` inventory will still match both persisted inventories even
though the Parquet, CSVs, and report were derived from different bytes. This defeats the claimed
immutable-source evidence boundary.

**Fix:** Restrict production `run`/`all` to the required supplied log path (or, if multiple supplied
logs are intentional, require the resolved input to be under `SUPPLIED_ROOT` and bind its live hash
to the manifest). During verification, validate the persisted `input.path` and recompute its hash;
reject it unless it is an allowed supplied input and agrees with both its manifest entry and the
live inventory.

### CR-02 [BLOCKER]: Parquet row-count evidence is self-declared, never verified

**File:** `pipeline/manifest.py:97-101,188-197,245-265`

**Issue:** `build_run_manifest()` sets the Parquet artifact's `row_count` from
`source_manifest.json["row_counts"]["parquet"]` rather than from the Parquet file. The verifier
only checks that this declared count is identical in the two manifests and that the ledger line
count matches `row_counts.input`; it never executes `COUNT(*)` on `logs_clean.parquet`. Therefore a
changed source-manifest Parquet count can be followed by `build_run_manifest()`, producing a new
self-consistent run ID and a passing verification despite a false declared analytical-row total.
The quality-table and analysis hashes do not repair this, because they are also rebuilt around the
same unverified claim.

**Fix:** During both manifest build and verification, query the generated Parquet directly (for
example, `SELECT COUNT(*) FROM read_parquet(?)`) and require it to equal the declared Parquet count.
Also derive/check ACCEPT+REPAIR counts from the ledger so the complete conservation equations are
verified independently of mutable manifest metadata. Add an adversarial regression that changes
only `row_counts.parquet`, rebuilds the run manifest, and expects verification to fail.

## Warnings

### WR-01 [WARNING]: Valid UTF-8 text containing U+FFFD is rejected as malformed text

**File:** `pipeline/ingest.py:52-68`

**Issue:** The decoder uses `errors="replace"` and then treats any replacement-character code point
(`\ufffd`) as proof of invalid UTF-8. A valid JSON record may legitimately contain U+FFFD in its
message or another field; this code rejects it as `TEXT_INVALID_UTF8`. Conversely, replacing invalid
bytes also loses the original byte representation in the ledger, weakening provenance for the row
that is rejected.

**Fix:** Decode strictly and handle `UnicodeDecodeError` explicitly. Preserve invalid raw bytes in a
lossless audit representation (such as a base64 field or a surrogate-escaped byte field) rather than
using the visual U+FFFD character as an error sentinel. Add tests for literal valid U+FFFD and an
actual invalid byte sequence.

### WR-02 [WARNING]: Accepted basic ISO-8601 offsets are recorded incorrectly

**File:** `pipeline/normalize.py:47-55`; `pipeline/__main__.py:149-173`

**Issue:** Validation accepts every offset form that `datetime.fromisoformat()` accepts, including
`2026-01-01T00:00:00+0700` and `...+07`. Both normalization paths then take the last six characters
to populate `timestamp_offset_raw`, yielding `0+0700` and `:00+07` respectively rather than the
supplied offset. This is an incorrect provenance field in otherwise accepted analytical rows.

**Fix:** Extract the offset with an explicit end-anchored ISO offset parser, or reject offset forms
outside the documented supported format during validation. Share that implementation between the
full pipeline and `trace`, and add tests for `+0700` and `+07` (or the chosen rejection behavior).

---

_Reviewed: 2026-08-11T05:18:16Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
