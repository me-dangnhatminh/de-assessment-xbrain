---
phase: 01-auditable-log-pipeline-analysis
plan: 03
subsystem: data pipeline
tags: [python, duckdb, parquet, sha256, data-quality, pytest]
requires:
  - phase: 01-02
    provides: provenance-first validation, dispositions, and duplicate handling
provides:
  - Immutable supplied-file SHA-256 inventory and generated-output guard
  - Deterministic normalization, quality ledger, typed Parquet, schema, and source manifest
  - Runnable integrity and full evidence-publication CLI stages
affects: [phase-01-analysis, static-sql, reviewer-evidence]
actuals:
  tokens: 581328
  tasks: 3
  commits: 5
tech-stack:
  added: []
  patterns: [atomic same-directory writes, source inventory before/after, fixed DuckDB Parquet schema]
key-files:
  created:
    - pipeline/integrity.py
    - pipeline/normalize.py
    - pipeline/write_outputs.py
    - tests/pipeline/test_pipeline_outputs.py
    - data/processed/logs_clean.parquet
    - data/evidence/phase1/source_manifest.json
    - data/evidence/phase1/quality_ledger.jsonl
    - data/evidence/phase1/schema.json
  modified:
    - pipeline/__main__.py
key-decisions:
  - "Represent valid timestamp conversions as Normalization evidence, never as repairs."
  - "Publish only ACCEPT and REPAIR rows to a source-line-ordered, typed Parquet dataset."
  - "Use a sorted full supplied-file inventory before and after each run to prove immutable-source integrity."
patterns-established:
  - "Generated evidence is canonical JSON/JSONL or fixed-schema Parquet and is atomically replaced."
  - "Every physical source line remains in the ledger while analytical records alone cross the Parquet boundary."
requirements-completed: [RPRO-02, PIPE-04, PIPE-05, PIPE-06]
coverage:
  - id: D1
    description: Immutable supplied-file inventory and output-root guard.
    requirement: RPRO-02
    verification:
      - kind: integration
        ref: tests/pipeline/test_pipeline_outputs.py#test_integrity_inventory_is_sorted_and_rejects_supplied_output_roots
        status: pass
    human_judgment: false
  - id: D2
    description: Deterministic per-line quality ledger with normalization provenance.
    requirement: PIPE-04
    verification:
      - kind: integration
        ref: tests/pipeline/test_pipeline_outputs.py#test_full_run_conservation_reconciles_all_lines_and_keeps_rejects_out_of_parquet
        status: pass
    human_judgment: false
  - id: D3
    description: Reconciled analytical boundary and byte-identical fresh-root reruns.
    requirement: PIPE-05
    verification:
      - kind: integration
        ref: tests/pipeline/test_pipeline_outputs.py#test_full_run_is_deterministic_across_fresh_roots_and_integrity_command_reports_totals
        status: pass
    human_judgment: false
  - id: D4
    description: Fixed-schema typed Parquet plus reviewer-readable schema rationale.
    requirement: PIPE-06
    verification:
      - kind: integration
        ref: tests/pipeline/test_pipeline_outputs.py#test_atomic_writers_emit_fixed_schema_and_stable_bytes
        status: pass
    human_judgment: false
duration: 14 min
completed: 2026-08-11
status: complete
---

# Phase 01 Plan 03: Deterministic Evidence Publication Summary

**Immutable-source log normalization and a reconciled, typed Parquet evidence snapshot with source-line provenance.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-08-11T03:31:34Z
- **Completed:** 2026-08-11T03:46:30Z
- **Tasks:** 3/3
- **Files modified:** 9

## Accomplishments

- Added UTC timestamp and ERROR-only semantic normalization that preserves raw values, treats valid conversions as normalizations, and exposes unclassified errors.
- Added source-inventory guards, full-run conservation checks, atomic writer utilities, and independent `integrity`/`run` CLI stages.
- Published the canonical ledger, schema, source manifest, and 2,839-row typed Parquet snapshot from the production run path.

## Verification

- Full pipeline suite: `20 passed in 33.51s`.
- Pipeline lint and format checks: passed.
- Canonical run: `accept=2839`, `repair=0`, `reject=84`, `unclassified_errors=35`.
- Fresh-root rerun byte-matched all four canonical artifacts; Parquet covers 2026-07-27 through 2026-08-02.
- `git diff --exit-code -- docs/onboard` passed.

## Task Commits

1. **Task 1: Normalize accepted analytical rows and prove deterministic writers** - `825a754` (test), `24ba49e` (feat)
2. **Task 2: Wire the full run with source integrity and row conservation** - `391109a` (test), `9bc7631` (feat)
3. **Task 3: Publish the canonical base evidence snapshot** - `860bcc2` (feat)

## Files Created/Modified

- `pipeline/normalize.py` - UTC and stable ERROR-message normalization.
- `pipeline/write_outputs.py` - atomic canonical JSON/JSONL/CSV/schema/Parquet writers.
- `pipeline/integrity.py` - supplied-file inventory, hashing, and output-root protection.
- `pipeline/__main__.py` - full immutable-source run and integrity CLI stages.
- `tests/pipeline/test_pipeline_outputs.py` - normalization, writer, conservation, and determinism contracts.
- `data/processed/logs_clean.parquet` - canonical 2,839-row analytical dataset.
- `data/evidence/phase1/` - source manifest, full ledger, and fixed schema evidence.

## Decisions Made

- Valid timestamp representation changes are recorded as normalizations; no canonical record is claimed as repaired without a lossless, mechanical repair rule.
- The quality ledger retains every physical source line, while only ACCEPT/REPAIR records enter the analytical dataset.
- Source integrity uses a complete, sorted inventory of every regular file under `docs/onboard` before and after generated writes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the Parquet DATE contract assertion**
- **Found during:** Task 1
- **Issue:** DuckDB returns a typed `date`, not a string, when reading the declared Parquet DATE column.
- **Fix:** Assert the stable ISO representation of the typed date.
- **Files modified:** `tests/pipeline/test_pipeline_outputs.py`
- **Verification:** Focused normalization/writer suite passed.
- **Committed in:** `24ba49e`

**2. [Rule 1 - Bug] Avoided legacy tracer writer shadowing**
- **Found during:** Task 2
- **Issue:** The existing single-record tracer helper shadowed the imported multi-row writer used by `run`.
- **Fix:** Aliased the multi-row writer at its integration call site.
- **Files modified:** `pipeline/__main__.py`
- **Verification:** Full-run conservation and fresh-root tests passed.
- **Committed in:** `9bc7631`

**3. [Rule 3 - Blocking Integration] Batched Parquet inserts for the full canonical dataset**
- **Found during:** Task 2
- **Issue:** Row-by-row DuckDB insertion made deterministic full-run verification unnecessarily slow for 2,839 records.
- **Fix:** Inserted ordered column lists through one DuckDB statement before the fixed Parquet copy.
- **Files modified:** `pipeline/write_outputs.py`
- **Verification:** Fresh-root artifacts remained byte-identical and the complete suite passed.
- **Committed in:** `9bc7631`

**Total deviations:** 3 auto-fixed (2 Rule 1, 1 Rule 3).
**Impact on plan:** All fixes preserve the planned interfaces and improve correctness or completion reliability without scope expansion.

## Issues Encountered

None.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The immutable, reconciled base evidence is ready for static SQL analysis and reviewer-facing reporting in Plan 01-04.

## Self-Check: PASSED

- All nine declared production, test, and canonical evidence files exist.
- All five task commits (`825a754`, `24ba49e`, `391109a`, `9bc7631`, `860bcc2`) exist in Git history.
