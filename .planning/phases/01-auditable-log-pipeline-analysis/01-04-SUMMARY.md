---
phase: 01-auditable-log-pipeline-analysis
plan: 04
subsystem: data pipeline analysis
tags: [python, duckdb, parquet, static-sql, csv, pytest]
requires:
  - phase: 01-03
    provides: immutable-source evidence, typed cleaned Parquet, and fixed output writers
provides:
  - Static, parameter-bound DuckDB SQL registry for all four customer analyses
  - Deterministic service ERROR-count and UTC daily-count CSV evidence
  - Locked, descriptive unusual-day heuristic with reconciled service contributions
affects: [phase-01-plan-05, phase-01-plan-06, reviewer-evidence]
actuals:
  tokens: 3911
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns: [static SQL registry, bound DuckDB paths, deterministic CSV result contracts]
key-files:
  created:
    - pipeline/analysis.py
    - pipeline/sql/01_service_error_counts.sql
    - pipeline/sql/02_daily_error_counts.sql
    - tests/pipeline/test_analysis.py
    - data/evidence/phase1/tables/01_service_error_counts.csv
    - data/evidence/phase1/tables/02_daily_error_counts.csv
  modified:
    - pipeline/__main__.py
key-decisions:
  - "Keep all customer aggregations in checked-in DuckDB SQL; Python only binds values, validates schemas, and serializes result rows."
  - "Resolve the highest-ERROR service by error-count descending then service ascending."
  - "Use UTC event_date_utc and a strict greater-than-two-times-seven-day-median descriptive rule, with service contributions but no causation claim."
patterns-established:
  - "AnalysisSpec fixes IDs, SQL paths, result paths, parameter contracts, and CSV schemas before later query implementations are added."
  - "Explicitly requested missing analysis SQL fails clearly; no-ID runs only implemented registry entries."
requirements-completed: [PIPE-07, PIPE-08, PIPE-11]
coverage:
  - id: D1
    description: Deterministic highest-ERROR service result generated from checked-in static SQL over cleaned Parquet.
    requirement: PIPE-07
    verification:
      - kind: integration
        ref: tests/pipeline/test_analysis.py#test_service_error_counts_uses_static_sql_and_returns_deterministic_answer
        status: pass
      - kind: other
        ref: python -m pipeline analyze --analysis-id service-error-counts --output-root data
        status: pass
    human_judgment: false
  - id: D2
    description: Seven UTC daily ERROR counts with a strict two-times-median descriptive flag and reconciled service contributions.
    requirement: PIPE-08
    verification:
      - kind: integration
        ref: tests/pipeline/test_analysis.py#test_daily_error_counts_uses_seven_utc_dates_and_cleaned_error_rows
        status: pass
      - kind: integration
        ref: tests/pipeline/test_analysis.py#test_daily_error_counts_applies_only_the_strict_descriptive_median_rule
        status: pass
    human_judgment: false
  - id: D3
    description: Fixed analysis registry and parameter-bound static SQL evidence contracts for subsequent analysis and reporting work.
    requirement: PIPE-11
    verification:
      - kind: integration
        ref: tests/pipeline/test_analysis.py#test_service_error_counts_registry_declares_all_final_contracts
        status: pass
      - kind: integration
        ref: tests/pipeline/test_analysis.py#test_analysis_registry_rejects_an_explicit_unimplemented_query
        status: pass
    human_judgment: false
duration: 8 min
completed: 2026-08-11
status: complete
---

# Phase 01 Plan 04: Static SQL Analysis Summary

**Parameter-bound DuckDB SQL produces deterministic highest-ERROR service and seven-day UTC daily-error evidence from the typed cleaned Parquet dataset.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-08-11T03:51:42Z
- **Completed:** 2026-08-11T03:59:28Z
- **Tasks:** 2/2
- **Files modified:** 7

## Accomplishments

- Declared the final four-ID analysis registry with fixed SQL paths, output paths, parameter contracts, and expected CSV schemas.
- Published the deterministic service ERROR ranking: `payment-api` is first with 139 cleaned ERROR records; the five service rows reconcile to 287 cleaned ERROR records.
- Published seven daily UTC ERROR rows from 2026-07-27 through 2026-08-02. The 2026-07-30 count of 140 is the only day strictly above twice the seven-day median of 27, with contributions that sum to 140.

## Verification

- Focused analysis suite: `9 passed in 10.54s`.
- Remaining pipeline suite: `28 passed, 1 deselected in 22.88s`; the long fresh-root determinism case passed separately: `1 passed in 21.85s`.
- Ruff check and format check for `pipeline/` and `tests/pipeline/`: passed.
- Selected-ID and no-ID analysis commands generated both recorded tables; byte-stable daily rerun SHA-256: `0f782ff388dc048365b13f5e4aa73342b32d6bc58eebcbf4fcc5aaa34bc37593`.
- Independent checks confirmed headers, service ordering, Parquet ERROR-total reconciliation, seven UTC dates, strict threshold behavior, contribution sums, no causation field, and no modification to `docs/onboard`.

## Task Commits

1. **Task 1: Reproduce the highest-ERROR service through the final static-SQL registry** - `451062e` (test), `0d2022f` (feat)
2. **Task 2: Reproduce UTC daily counts and the locked unusual-day heuristic** - `7a2ce3e` (test), `75a13c3` (feat)
3. **Follow-up coverage: reject explicitly requested unavailable registry IDs** - `fd1710a` (test)

## Files Created/Modified

- `pipeline/analysis.py` - fixed analysis registry, parameter binding, schema assertion, and deterministic CSV execution.
- `pipeline/__main__.py` - `analyze` CLI command for selected or available registered analyses.
- `pipeline/sql/01_service_error_counts.sql` - ranked cleaned ERROR counts by service with stable tie-breaking.
- `pipeline/sql/02_daily_error_counts.sql` - UTC window, median, strict descriptive flag, ratio, and service contributions.
- `tests/pipeline/test_analysis.py` - integration contracts for SQL-only results, CLI behavior, determinism, UTC normalization, and interpretation bounds.
- `data/evidence/phase1/tables/01_service_error_counts.csv` - committed highest-service evidence.
- `data/evidence/phase1/tables/02_daily_error_counts.csv` - committed daily-error evidence.

## Decisions Made

- Customer aggregates remain in checked-in SQL; Python does not recalculate counts or medians.
- The daily result exposes a descriptive `is_unusual_by_2x_median_rule` boolean and `error_count_to_median_ratio`, never a statistical anomaly or causal conclusion.
- The registry is complete now, while its no-ID execution intentionally limits itself to checked-in SQL implementations until Plan 05 adds the remaining queries.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Prepared the selected-ID CLI test with its required cleaned Parquet input**
- **Found during:** Task 1
- **Issue:** The original CLI test used a fresh output root without the cleaned Parquet that the analysis command correctly requires.
- **Fix:** Generated the normal immutable-source run output before invoking the selected-ID command.
- **Files modified:** `tests/pipeline/test_analysis.py`
- **Verification:** The service-analysis CLI and byte-stability contracts passed.
- **Committed in:** `0d2022f`

**2. [Rule 2 - Missing Critical Coverage] Added an explicit unavailable-analysis regression guard**
- **Found during:** Final verification
- **Issue:** The registry behavior for an explicitly requested but unimplemented SQL ID was implemented but had no direct regression test.
- **Fix:** Added an assertion that the CLI returns an actionable failure rather than silently omitting the requested evidence.
- **Files modified:** `tests/pipeline/test_analysis.py`
- **Verification:** Focused analysis suite passed.
- **Committed in:** `fd1710a`

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 2).
**Impact on plan:** Both changes preserve the planned interface and make the evidence contract more reliable without expanding scope.

## Issues Encountered

`uv` is unavailable on the host shell, so all planned commands were run with the locked `.venv/bin/python` runtime. The same locked project dependencies were used.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 05 can add `03_top_normalized_errors.sql` and `04_quality_reconciliation.sql` without changing the existing registry IDs, paths, schemas, or runner contract.

## TDD Gate Compliance

Passed: Task 1 and Task 2 each have a failing-test commit followed by a feature commit.

## Self-Check: PASSED

- All seven declared production, test, and evidence files exist.
- All five task and follow-up commits exist in Git history.
