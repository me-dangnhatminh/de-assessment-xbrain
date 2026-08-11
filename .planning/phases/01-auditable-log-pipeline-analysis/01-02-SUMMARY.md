---
phase: 01-auditable-log-pipeline-analysis
plan: 02
subsystem: data-pipeline
tags: [python, jsonl, validation, provenance, sha256, pytest, ruff]
requires:
  - phase: 01-01
    provides: "Locked Python environment and immutable single-line tracer"
provides:
  - "Typed source, issue, normalization, ledger, disposition, and clean-record contracts"
  - "Bounded provenance-first JSONL ingestion and canonical full-record digests"
  - "Deterministic full-source validation ledger with conservative dispositions and duplicate references"
affects: ["Phase 01 plans 03-06", pipeline, data-quality-evidence, Parquet]
actuals:
  tokens: 8405
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - "Envelope each physical line before parsing and retain one ordered ledger row."
    - "Collect every issue before resolving explicit REJECT > REPAIR > ACCEPT precedence."
    - "Identify duplicates using a SHA-256 digest of the complete canonical parsed object."
key-files:
  created:
    - pipeline/models.py
    - pipeline/ingest.py
    - pipeline/validation.py
    - tests/pipeline/test_validation.py
  modified:
    - pipeline/__main__.py
key-decisions:
  - "Enforce INFO, WARN, and ERROR as fixed levels while allowing any non-empty service because no authoritative service allowlist exists."
  - "Record unexpected fields as visible ACCEPT-level issues and preserve trace_id as optional provenance."
  - "Keep a first-class REPAIR disposition for lossless policy cases while the canonical source honestly reports zero repairs."
patterns-established:
  - "Validation uses frozen dataclasses and stable English issue policies for downstream evidence consumers."
  - "Generated validation ledgers serialize nested issues in source-line and policy order."
requirements-completed: [PIPE-01, PIPE-02, PIPE-03, PIPE-04]
coverage:
  - id: D1
    description: "Every physical input line is enveloped before parsing and malformed JSON remains source-traceable."
    requirement: PIPE-01
    verification:
      - kind: unit
        ref: "tests/pipeline/test_validation.py#test_malformed_json_has_a_rejecting_provenance_envelope"
        status: pass
      - kind: integration
        ref: ".venv/bin/python -m pipeline validate --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root <temp>"
        status: pass
    human_judgment: false
  - id: D2
    description: "Required fields, timestamp awareness, level policy, optional trace_id, and unexpected fields have explicit deterministic policies."
    requirement: PIPE-02
    verification:
      - kind: unit
        ref: "tests/pipeline/test_validation.py#test_required_types_timestamps_levels_and_content_have_stable_issues"
        status: pass
      - kind: unit
        ref: "tests/pipeline/test_validation.py#test_unknown_service_is_valid_trace_id_is_optional_and_extra_fields_are_visible"
        status: pass
    human_judgment: false
  - id: D3
    description: "Exact duplicate records are rejected with a cross-reference to their first retained source line, after all issues are collected."
    requirement: PIPE-03
    verification:
      - kind: unit
        ref: "tests/pipeline/test_validation.py#test_duplicate_records_reference_the_first_retained_source_line"
        status: pass
      - kind: unit
        ref: "tests/pipeline/test_validation.py#test_all_issues_are_retained_and_reject_overrides_repair"
        status: pass
    human_judgment: false
  - id: D4
    description: "The canonical source validates deterministically with one ledger row per physical line and zero invented repairs."
    requirement: PIPE-04
    verification:
      - kind: integration
        ref: "tests/pipeline/test_validation.py#test_canonical_source_has_no_repairs_and_validation_is_deterministic"
        status: pass
      - kind: other
        ref: "source-lines=2923 ledger-rows=2923 malformed-json=18 exact-duplicates=28 repairs=0"
        status: pass
    human_judgment: false
duration: 4min
completed: 2026-08-11
status: complete
---

# Phase 01 Plan 02: Full Validation and Disposition Summary

**A provenance-first JSONL validator produces one deterministic ledger decision per source line, with explicit data-quality issues and exact-duplicate evidence.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-11T03:24:55Z
- **Completed:** 2026-08-11T03:28:57Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Added frozen contracts for source envelopes, issues, normalizations, ledger entries, dispositions, and future clean analytical rows.
- Implemented byte-bounded physical-line ingestion, pre-parse provenance, stable schema/timestamp/level checks, and an independently runnable `python -m pipeline validate` command.
- Added canonical full-record duplicate detection, D-05 action precedence, deterministic nested ledger output, and a deliberately zero-repair canonical run.

## Task Commits

1. **Task 1 (RED): Make malformed and schema-invalid lines visible through the validate command** - `fb5e5a7` (`test`)
2. **Task 1 (GREEN): Make malformed and schema-invalid lines visible through the validate command** - `c95fbcd` (`feat`)
3. **Task 2 (RED): Complete duplicate handling, multi-issue precedence, and conservative repair** - `0f9f89b` (`test`)
4. **Task 2 (GREEN): Complete duplicate handling, multi-issue precedence, and conservative repair** - `7a5025c` (`feat`)

## Files Created/Modified

- `pipeline/models.py` - Immutable validation, ledger, and clean-record contracts.
- `pipeline/ingest.py` - Provenance-first bounded line reader, JSON parser, and canonical digest function.
- `pipeline/validation.py` - Stable issue catalogue, comprehensive issue collection, and disposition precedence.
- `pipeline/__main__.py` - Full-input `validate` subcommand while retaining the existing tracer behavior.
- `tests/pipeline/test_validation.py` - Unit and real-source tests for line accounting, policy, duplicates, precedence, and determinism.

## Decisions Made

- Enforced `INFO|WARN|ERROR` but deliberately did not reject a non-empty unknown service, because the supplied material defines no authoritative service allowlist.
- Computed duplicate identities from a canonical serialization of the complete parsed object, so formatting and input key order cannot hide an exact duplicate.
- Kept the REPAIR branch a first-class, test-covered disposition but did not manufacture a canonical repair when no supplied defect is losslessly provable.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test correctness] Included the missing-required-field issue in the multi-issue assertion**
- **Found during:** Task 1
- **Issue:** The initial test intentionally supplied `request_id=None` but omitted `REQUIRED_FIELD_MISSING` from its expected issue set.
- **Fix:** Corrected the assertion so the test proves every independently applicable issue remains visible.
- **Files modified:** `tests/pipeline/test_validation.py`
- **Verification:** Focused validation and tracer tests pass.
- **Committed in:** `c95fbcd`

**Total deviations:** 1 auto-fixed (1 Rule 1).
**Impact on plan:** The correction strengthened the D-05 evidence without changing the planned implementation scope.

## Verification

- `.venv/bin/python -m pytest tests/pipeline/test_validation.py tests/pipeline/test_tracer.py -q` — passed (13 tests).
- `.venv/bin/python -m ruff check pipeline/models.py pipeline/ingest.py pipeline/validation.py pipeline/__main__.py tests/pipeline/test_validation.py` — passed.
- `.venv/bin/python -m ruff format --check pipeline/models.py pipeline/ingest.py pipeline/validation.py pipeline/__main__.py tests/pipeline/test_validation.py` — passed.
- Full temporary-root validation — passed: 2,923 source lines and 2,923 ordered ledger rows; 18 malformed JSON lines, 28 exact duplicates, and 0 repairs.
- Fresh temporary-root ledger rerun — byte-identical (`942c7e2bbc9942a243fe911c3e62e0a2f06854b24f81e23f1cc5efed1429bb0d`).
- `git diff --exit-code -- docs/onboard` and source SHA-256 before/after validation — passed.

## Known Stubs

None.

## Issues Encountered

The host shell does not expose `uv`; per the previous wave's verified fallback, the locked project `.venv` executed the same pytest and Ruff commands. This did not change committed dependency or command documentation.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

Plan 03 can consume the established contracts unchanged to normalize ACCEPT/REPAIR records and publish deterministic ledger and Parquet evidence.

## Self-Check: PASSED

- All five planned pipeline/test artifacts exist.
- All four TDD RED/GREEN commits are present in Git history.
- The latest focused validation and tracer suite passed (13 tests).
