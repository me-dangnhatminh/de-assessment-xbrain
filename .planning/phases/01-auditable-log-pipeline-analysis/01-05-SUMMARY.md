---
phase: 01-auditable-log-pipeline-analysis
plan: 05
subsystem: data pipeline analysis
tags: [python, duckdb, parquet, jsonl, static-sql, csv, pytest]
requires:
  - phase: 01-04
    provides: static SQL registry, parameter-bound DuckDB execution, and deterministic CSV evidence writers
provides:
  - Deterministic top-three semantic ERROR-type SQL with secondary service evidence
  - Quality reconciliation SQL that distinguishes issue occurrences from final-action records
  - Committed third and fourth customer-analysis tables with dual conservation checks
affects: [phase-01-plan-06, reviewer-evidence, pipeline-report]
actuals:
  tokens: 4721
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [semantic primary ranking, deterministic JSON service contributions, dual-source SQL reconciliation]
key-files:
  created:
    - pipeline/sql/03_top_normalized_errors.sql
    - pipeline/sql/04_quality_reconciliation.sql
    - data/evidence/phase1/tables/03_top_normalized_errors.csv
    - data/evidence/phase1/tables/04_quality_reconciliation.csv
  modified:
    - pipeline/analysis.py
    - tests/pipeline/test_analysis.py
key-decisions:
  - "Rank only ERROR primary error_type values, use count-descending/name-ascending ties, and retain services as deterministic secondary JSON evidence."
  - "Bind both quality-ledger JSONL and cleaned Parquet paths so record dispositions and analytical-row conservation remain independently auditable."
patterns-established:
  - "Customer-result schemas are declared in AnalysisSpec and asserted before deterministic CSV publication."
  - "Quality SQL keeps issue occurrences, distinct affected records, final-action totals, and conservation equations in separate rows."
requirements-completed: [PIPE-09, PIPE-10, PIPE-11]
coverage:
  - id: D1
    description: Deterministic top-three normalized ERROR-type ranking with service contributions and visible unclassified count.
    requirement: PIPE-09
    verification:
      - kind: integration
        ref: tests/pipeline/test_analysis.py#test_top_normalized_errors_ranks_primary_types_and_retains_service_evidence
        status: pass
      - kind: integration
        ref: tests/pipeline/test_analysis.py#test_top_normalized_errors_has_deterministic_tie_boundary_and_error_only_filter
        status: pass
    human_judgment: false
  - id: D2
    description: Ledger issue occurrences and final-action record totals, including explicit zero repairs and both conservation equations.
    requirement: PIPE-10
    verification:
      - kind: integration
        ref: tests/pipeline/test_analysis.py#test_quality_reconciliation_separates_actions_issues_and_conservation
        status: pass
      - kind: integration
        ref: tests/pipeline/test_analysis.py#test_quality_reconciliation_committed_evidence_is_stable_and_complete
        status: pass
    human_judgment: false
  - id: D3
    description: One no-ID command regenerates all four static SQL evidence tables byte-stably.
    requirement: PIPE-11
    verification:
      - kind: e2e
        ref: .venv/bin/python -m pipeline analyze --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data
        status: pass
    human_judgment: false
duration: 8 min
completed: 2026-08-11
status: complete
---

# Phase 01 Plan 05: Complete Static SQL Analysis Summary

**Four parameter-bound DuckDB queries now publish deterministic customer evidence: semantic ERROR rankings, secondary service contributions, and auditable quality reconciliation.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-08-11T04:03:59Z
- **Completed:** 2026-08-11T04:11:29Z
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments

- Published the top three cleaned semantic ERROR types with deterministic count/name ordering: `CONNECTION_TIMEOUT` (114), `HTTP_502` (41), and `NULL_POINTER` (37). Each row preserves service contributions and the visible `UNCLASSIFIED_ERROR` count of 35.
- Published a quality table that reports final-action records separately from issue occurrences, including explicit `REPAIR=0`, and proves `2923 = 2839 + 0 + 84` plus `2839 = 2839 + 0` analytical-row conservation.
- Completed the static analysis registry so one no-ID command regenerates all four committed CSV tables using only bound inputs and checked-in SQL.

## Verification

- `.venv/bin/python -m pytest -q` — **35 passed** in 45.82s.
- `.venv/bin/python -m ruff check pipeline tests/pipeline` — passed.
- `.venv/bin/python -m ruff format --check pipeline tests/pipeline` — passed.
- No-ID analysis command regenerated all four tables; two successive table-hash inventories were identical. Table 03 SHA-256: `15af445b8bd6502121b2f6f64ebe9534db4591b55906158b73080e92d0dcfb90`; Table 04 SHA-256: `31bcfd38c568a779cb25cd576fc98e0eb9db956e624763cb528983d153c87e59`.
- Explicit acceptance checks confirmed three primary rows, error-only taxonomy, visible unclassified count, explicit ACCEPT/REPAIR/REJECT rows, and two true conservation checks.

## Task Commits

1. **Task 1: Reproduce the top three semantic ERROR types and associated services** - `c52f9f1` (test), `f6c0e18` (feat)
2. **Task 2: Reconcile issue occurrences, final actions, and cleaned rows** - `688873a` (test), `345fb84` (feat)

## Files Created/Modified

- `pipeline/analysis.py` - completes the result schemas and binds the ledger/Parquet inputs required by each static query.
- `pipeline/sql/03_top_normalized_errors.sql` - ranks primary semantic ERROR types with stable service-contribution JSON.
- `pipeline/sql/04_quality_reconciliation.sql` - aggregates action records and issue occurrences independently, then emits conservation checks.
- `tests/pipeline/test_analysis.py` - validates top-three boundaries, service totals, unclassified visibility, zero repairs, counting-unit separation, and stable evidence.
- `data/evidence/phase1/tables/03_top_normalized_errors.csv` - committed answer for customer question three.
- `data/evidence/phase1/tables/04_quality_reconciliation.csv` - committed answer for customer question four.

## Decisions Made

- Primary ranking uses `error_type`; service remains secondary structured evidence, preventing embedded IDs, codes, and paths from fragmenting the top-three answer.
- Quality reconciliation binds both the ledger and cleaned Parquet. This keeps final dispositions distinct from issue occurrences while mechanically proving both conservation equations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Completed the quality-query input contract**
- **Found during:** Task 2
- **Issue:** The prior registry placeholder supplied only the ledger path, which cannot prove that accepted plus repaired records equal the cleaned Parquet row count.
- **Fix:** Declared and bound both `ledger_path` and `parquet_path` for quality reconciliation; the query now emits the analytical-row conservation result from both sources.
- **Files modified:** `pipeline/analysis.py`, `pipeline/sql/04_quality_reconciliation.sql`, `tests/pipeline/test_analysis.py`
- **Verification:** Quality contracts and the complete 35-test suite passed.
- **Committed in:** `345fb84`

**2. [Rule 1 - Bug] Updated the unavailable-analysis regression after implementation**
- **Found during:** Task 2 final verification
- **Issue:** A Plan 04 test correctly treated `top-normalized-errors` as unavailable before its SQL existed, but it became an invalid expectation once Task 1 implemented that ID.
- **Fix:** The guard now requests a genuinely unknown analysis ID and confirms the same actionable failure behavior.
- **Files modified:** `tests/pipeline/test_analysis.py`
- **Verification:** Complete analysis suite and full repository suite passed.
- **Committed in:** `345fb84`

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 1).
**Impact on plan:** Both changes are required for a truthful, complete analysis contract and do not expand the planned scope.

## Issues Encountered

`uv` is unavailable on the host shell, so planned commands used the checked-in locked `.venv/bin/python` runtime.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 06 can render reports and manifest evidence from four checked-in, deterministic static SQL tables without manual aggregation.

## Self-Check: PASSED

- All six planned source, test, and evidence files exist.
- All four TDD task commits exist in Git history.
- No stubs, skipped tests, unrun verifies, or unplanned security-relevant surfaces were found.
