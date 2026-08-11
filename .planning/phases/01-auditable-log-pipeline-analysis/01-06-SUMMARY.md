---
phase: 01-auditable-log-pipeline-analysis
plan: 06
subsystem: data pipeline evidence and reproducibility
tags: [python, duckdb, parquet, manifest, markdown, make, pytest, ruff]
requires:
  - phase: 01-05
    provides: Four deterministic parameter-bound SQL result tables and quality reconciliation evidence
provides:
  - Content-linked Phase 1 run manifest with hashes, row counts, command metadata, and SQL/result links
  - Evidence-only reviewer report that traces every customer answer to generated artifacts
  - Canonical locked-environment Make workflow with safe clean-root regeneration and verification
affects: [phase-02, phase-03, phase-04, reviewer-handoff]
actuals:
  tokens: 13421
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [content-derived run IDs, evidence-only report rendering, allowlisted generated-output cleanup, staged reviewer commands]
key-files:
  created:
    - pipeline/manifest.py
    - pipeline/report.py
    - Makefile
    - tests/pipeline/test_evidence.py
    - tests/pipeline/test_end_to_end.py
    - data/evidence/phase1/report.md
    - data/evidence/phase1/run_manifest.json
  modified:
    - pipeline/__main__.py
    - README.md
key-decisions:
  - "Render reviewer claims from generated CSV evidence and manifest metadata, never by querying Parquet or manually aggregating values."
  - "Derive the run ID from stable manifest content and omit wall-clock fields so the committed snapshot remains byte-stable."
  - "Allow --clean only for exact known Phase 1 artifact paths below a validated generated root; refuse repository and supplied-input roots."
patterns-established:
  - "A report cites analysis ID, SQL path, result path, cleaned-dataset hash, and relevant row counts beside every answer."
  - "The all command performs source checks around deterministic stage execution and then verifies the finalized manifest."
requirements-completed: [RPRO-01, RPRO-02, PIPE-05, PIPE-06, PIPE-07, PIPE-08, PIPE-09, PIPE-10, PIPE-11]
coverage:
  - id: D1
    description: Deterministic run manifest and evidence-only Markdown report for all four customer answers.
    requirement: PIPE-11
    verification:
      - kind: integration
        ref: tests/pipeline/test_evidence.py
        status: pass
      - kind: other
        ref: make verify-phase1
        status: pass
    human_judgment: false
  - id: D2
    description: Canonical locked reviewer workflow with independently runnable stages and constrained output cleanup.
    requirement: RPRO-01
    verification:
      - kind: e2e
        ref: tests/pipeline/test_end_to_end.py#test_all_regenerates_deterministic_evidence_without_mutating_inputs
        status: pass
      - kind: other
        ref: make verify-phase1
        status: pass
    human_judgment: false
  - id: D3
    description: Source immutability, deterministic evidence regeneration, and manifest consistency checks.
    requirement: RPRO-02
    verification:
      - kind: e2e
        ref: make verify-phase1
        status: pass
    human_judgment: false
duration: 17 min
completed: 2026-08-11
status: complete
---

# Phase 01 Plan 06: Reviewer Evidence and Canonical Workflow Summary

**A deterministic manifest, evidence-only report, and locked Make workflow now let a reviewer regenerate and trace every Phase 1 customer answer from immutable inputs.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-08-11T04:14:49Z
- **Completed:** 2026-08-11T04:31:57Z
- **Tasks:** 2/2
- **Files modified:** 9

## Accomplishments

- Published `run_manifest.json` with a content-derived run ID, source inventory reference, runtime metadata, exact commands, artifact hashes, row counts, and SQL-to-result analysis links.
- Published an English reviewer report that reads only generated evidence and places a direct SQL/result/hash/count/analysis-ID chain beside all four customer answers.
- Added `report`, `verify`, and `all` CLI stages, safe allowlisted cleanup, canonical Make targets, and English clean-checkout instructions.
- Proved clean-root deterministic regeneration and source immutability; the complete `make verify-phase1` gate passed with 44 tests.

## Verification

- `make verify-phase1` — passed: regenerated the complete snapshot, checked the committed lock/fallback, ran Ruff checks and formatting, ran **44 passed** tests, and confirmed `docs/onboard` has no Git diff.
- `tests/pipeline/test_evidence.py` — manifest/report contracts and artifact, query, count, and link tampering checks passed.
- `tests/pipeline/test_end_to_end.py` — canonical all-command, safe cleanup, stage argument, Makefile, and README contracts passed.

## Task Commits

1. **Task 1: Render a content-linked manifest and the primary reviewer report** — `fb13d54` (test), `8d675e5` (feat)
2. **Task 2: Expose canonical and stage commands and prove clean-checkout regeneration** — `aed6399` (test), `b792db8` (feat)

## Files Created/Modified

- `pipeline/manifest.py` — builds and verifies deterministic content-linked evidence manifests.
- `pipeline/report.py` — renders the primary English report from CSV and metadata evidence only.
- `pipeline/__main__.py` — supplies report, verify, all, and guarded cleanup command handlers.
- `Makefile` and `README.md` — expose the locked canonical command, independent stages, evidence map, findings, and honest boundaries.
- `tests/pipeline/test_evidence.py` and `tests/pipeline/test_end_to_end.py` — cover evidence integrity and clean-root workflow contracts.
- `data/evidence/phase1/report.md` and `data/evidence/phase1/run_manifest.json` — committed direct-review evidence snapshot.

## Decisions Made

- Report values are rendered from generated CSVs and manifest metadata, which prevents a second aggregation path and keeps every claim traceable.
- Manifest content is stable and content-derived, with no wall-clock field, so a same-input rerun produces the same snapshot.
- Cleanup is a narrow allowlist under a validated generated root; it cannot remove supplied inputs or the project root.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Imported the complete SQL registry for the cleanup allowlist**
- **Found during:** Task 2
- **Issue:** The new generated-path allowlist referenced `ANALYSIS_SPECS` before importing it, preventing CLI loading.
- **Fix:** Imported the existing registry alongside the analysis runner.
- **Files modified:** `pipeline/__main__.py`
- **Verification:** `tests/pipeline/test_end_to_end.py` passed.
- **Committed in:** `b792db8`

**2. [Rule 1 - Bug] Made orchestration safe for namespaces without an analysis selector**
- **Found during:** Task 2
- **Issue:** `all` reused `cmd_analyze`, but its argument namespace has no `analysis_id` attribute.
- **Fix:** Treated a missing selector as the existing all-analyses path.
- **Files modified:** `pipeline/__main__.py`
- **Verification:** clean-root all-command test and `make verify-phase1` passed.
- **Committed in:** `b792db8`

**3. [Rule 1 - Bug] Preserved the existing integrity command invocation contract**
- **Found during:** Task 2 final verification
- **Issue:** Requiring `--output-root` on `integrity` broke an established independently runnable command that does not write outputs.
- **Fix:** Kept the shared option available while making it optional for `integrity`.
- **Files modified:** `pipeline/__main__.py`
- **Verification:** full suite passed with 44 tests.
- **Committed in:** `b792db8`

**4. [Rule 3 - Blocking issue] Added a checked-in virtual-environment fallback for this host**
- **Found during:** Task 2
- **Issue:** The host shell has no global `uv`, so a literal-only Make workflow could not run the mandatory verification gate.
- **Fix:** Kept the documented canonical `uv run --locked` path and made the Makefile use the pre-existing locked `.venv` only when `uv` is unavailable.
- **Files modified:** `Makefile`, `README.md`
- **Verification:** `make verify-phase1` passed with the fallback; clean reviewer instructions still begin with `uv sync --locked`.
- **Committed in:** `b792db8`

**Total deviations:** 4 auto-fixed (3 Rule 1, 1 Rule 3).
**Impact on plan:** All fixes preserve the planned evidence chain, safe cleanup boundary, and reviewer workflow without expanding Phase 1 scope.

## Issues Encountered

The host lacks a global `uv` executable. The committed Makefile transparently used the existing locked `.venv` fallback for local verification; the README retains the reviewer-facing `uv sync --locked` workflow.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 1 now has a complete deterministic evidence chain and reviewer workflow. Phase 2 can build its version-aware knowledge base without relying on undocumented pipeline state.

## Self-Check: PASSED

- All seven created evidence, implementation, build, and test files exist on disk.
- All four task commits (`fb13d54`, `8d675e5`, `aed6399`, and `b792db8`) exist in Git history.
- No stubs, skipped tests, unrun verification, or unmodeled security surfaces were found.
