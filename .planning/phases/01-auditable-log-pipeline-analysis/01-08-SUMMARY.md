---
phase: 01-auditable-log-pipeline-analysis
plan: 08
subsystem: pipeline-evidence
tags: [python, duckdb, parquet, sha256, manifest-verification, pytest]
requires:
  - phase: 01-07
    provides: live supplied-input inventory verification and deterministic Phase 1 manifests
provides:
  - Canonical production-input binding for `run` and `all`
  - Live input-descriptor authentication during manifest verification
  - DuckDB-measured Parquet cardinality and ledger-derived action conservation
affects: [phase-01-verification, reviewer-evidence, phase-02]
tech-stack:
  added: []
  patterns:
    - Reject untrusted production paths before cleanup or generated writes.
    - Derive integrity verdicts from live artifacts rather than mutually consistent manifests.
key-files:
  created:
    - .planning/phases/01-auditable-log-pipeline-analysis/01-08-SUMMARY.md
  modified:
    - pipeline/integrity.py
    - pipeline/__main__.py
    - pipeline/manifest.py
    - tests/pipeline/test_evidence.py
    - tests/pipeline/test_end_to_end.py
    - data/evidence/phase1/run_manifest.json
key-decisions:
  - "Allow production evidence only from the exact canonical supplied JSONL after path resolution."
  - "Authenticate persisted input descriptors against the live canonical file and supplied inventory."
  - "Measure Parquet and ledger totals live during verification rather than trusting manifest declarations."
requirements-completed: [RPRO-02, PIPE-05]
actuals:
  tokens: 8704
  tasks: 2
  commits: 6
metrics:
  duration: 22min
  completed: 2026-08-11
status: complete
---

# Phase 01 Plan 08: Canonical Evidence Integrity Summary

**Production evidence is now bound to the canonical supplied log, with verification deriving input identity and row conservation from live artifacts.**

## Performance

- **Duration:** 22 min
- **Tasks:** 2/2
- **Files modified:** 6
- **Commits:** 6

## Accomplishments

- Added a canonical supplied-log guard used by `run` and `all` before cleanup or generated writes.
- Authenticated the persisted input descriptor against the canonical path, its fresh SHA-256, and the source/live supplied inventories.
- Added DuckDB Parquet counting at manifest build and verification time.
- Derived ACCEPT, REPAIR, and REJECT totals from strict ledger parsing and enforced both conservation equations against both manifest layers.
- Added adversarial regressions for foreign inputs, forged descriptors, rebuilt count forgeries, malformed live evidence, and repeatability.

## Task Commits

1. **Task 1: Bind production evidence to the canonical supplied log end to end** — `53cc934` (RED tests), `eea731a` (implementation)
2. **Task 2: Prove row conservation from live Parquet and ledger contents** — `22581a9` (RED tests), `c897e34` (implementation), `f64cfd6` (malformed-evidence test completion)
3. **Canonical evidence refresh** — `c1de72f`

## Verification

- Focused canonical-input regressions — passed, including foreign repository-local input rejection, forged input descriptors, forged hashes, and repeatability.
- Focused live-conservation regressions — passed, including rebuilt source Parquet-count forgery, ledger-action tampering, malformed ledger entries, and malformed Parquet.
- `make verify-phase1` — completed pipeline regeneration, locked sync, Ruff check/format, manifest verification, and immutable supplied-input check.
- `uv run --locked python -m pipeline verify --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data` — passed.
- `git diff --exit-code -- docs/onboard` — passed.

## Decisions Made

- Canonical path authorization is an evaluator-facing production boundary; `trace` and `validate` remain fixture-friendly.
- Source and run manifests are untrusted declarations; the verifier recomputes the live file and artifact facts needed for its verdict.
- Ledger `final_action`, rather than nested issue occurrences, determines analytical row conservation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restored the run-inventory comparison after adding input binding**
- **Found during:** Task 1 focused verification
- **Issue:** The initial integration accidentally placed the existing run-inventory comparison inside the new input-binding helper.
- **Fix:** Restored the comparison to `_verify_source_inventory()` before continuing with input authentication.
- **Files modified:** `pipeline/manifest.py`
- **Commit:** `eea731a`

**2. [Rule 1 - Bug] Built a valid manifest before corrupting live Parquet in the malformed-evidence regression**
- **Found during:** Task 2 focused verification
- **Issue:** The initial test exercised a missing run manifest rather than the intended malformed Parquet boundary.
- **Fix:** Created the valid manifest before corruption so verification reaches the live Parquet count guard.
- **Files modified:** `tests/pipeline/test_evidence.py`
- **Commit:** `f64cfd6`

## Known Stubs

None.

## Next Phase Readiness

Phase 1 now has a fail-closed input and row-conservation boundary suitable for downstream knowledge-base work and reviewer verification.

## Self-Check: PASSED

Confirmed all planned files exist and commits `53cc934`, `eea731a`, `22581a9`, `c897e34`, `f64cfd6`, and `c1de72f` are present in Git history.
