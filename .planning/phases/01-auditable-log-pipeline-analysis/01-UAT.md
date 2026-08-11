---
status: complete
phase: 01-auditable-log-pipeline-analysis
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md, 01-05-SUMMARY.md, 01-06-SUMMARY.md, 01-07-SUMMARY.md, 01-08-SUMMARY.md]
started: 2026-08-11T17:07:28Z
updated: 2026-08-12T01:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Automated Coverage Confirmation (01-01..01-07)
expected: |
  Every deliverable from plans 01-01..01-07 below is covered by a passing
  automated verification (unit/integration/e2e test or checked-in command).
  Reviewer confirms the described behavior matches what was actually built and
  verified.
result: pass

### 2. Canonical Production-Input Guard (01-08)
expected: |
  `uv run --locked python -m pipeline verify --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data`
  succeeds with "run manifest verified"; a foreign or non-canonical input path
  is rejected before any cleanup or generated write; `git diff --exit-code -- docs/onboard`
  confirms supplied files remain untouched after regeneration.
result: pass

### 3. Fail-Closed Adversarial Verification (01-08)
expected: |
  Forged input descriptors, forged SHA-256 hashes, tampered ledger actions,
  rebuilt Parquet counts, and malformed ledger/Parquet files all cause `verify`
  to fail closed; a correct re-run passes consistently (repeatability).
result: pass

### 4. Approved locked Python toolchain resolves and synchronizes deterministically. [01-01 D1]
expected: `uv lock --check && uv sync --locked` succeeds against the committed lockfile.
result: pass
source: automated
coverage_id: D1
requirement: RPRO-01

### 5. One physical immutable source line is traced with source-line and SHA-256 evidence. [01-01 D2]
expected: `tests/pipeline/test_tracer.py#test_trace_preserves_source_provenance_and_normalizes_real_error` passes.
result: pass
source: automated
coverage_id: D2
requirement: RPRO-02

### 6. The tracer writes linked ledger, typed Parquet, static-SQL CSV, and manifest artifacts. [01-01 D3]
expected: `tests/pipeline/test_tracer.py#test_trace_writes_content_linked_ledger_parquet_sql_and_manifest` passes.
result: pass
source: automated
coverage_id: D3
requirement: PIPE-11

### 7. Fresh tracer output roots are byte-stable and writes under supplied inputs are rejected. [01-01 D4]
expected: `tests/pipeline/test_tracer.py#test_trace_is_stable_across_fresh_output_roots` and `#test_trace_rejects_output_inside_immutable_source_tree` pass.
result: pass
source: automated
coverage_id: D4
requirement: PIPE-05

### 8. Every physical input line is enveloped before parsing and malformed JSON remains source-traceable. [01-02 D1]
expected: `tests/pipeline/test_validation.py#test_malformed_json_has_a_rejecting_provenance_envelope` passes; `python -m pipeline validate --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root <temp>` runs cleanly.
result: pass
source: automated
coverage_id: D1
requirement: PIPE-01

### 9. Required fields, timestamp awareness, level policy, optional trace_id, and unexpected fields have explicit deterministic policies. [01-02 D2]
expected: `tests/pipeline/test_validation.py#test_required_types_timestamps_levels_and_content_have_stable_issues` and `#test_unknown_service_is_valid_trace_id_is_optional_and_extra_fields_are_visible` pass.
result: pass
source: automated
coverage_id: D2
requirement: PIPE-02

### 10. Exact duplicate records are rejected with a cross-reference to their first retained source line. [01-02 D3]
expected: `tests/pipeline/test_validation.py#test_duplicate_records_reference_the_first_retained_source_line` and `#test_all_issues_are_retained_and_reject_overrides_repair` pass.
result: pass
source: automated
coverage_id: D3
requirement: PIPE-03

### 11. The canonical source validates deterministically with one ledger row per physical line and zero invented repairs. [01-02 D4]
expected: `tests/pipeline/test_validation.py#test_canonical_source_has_no_repairs_and_validation_is_deterministic` passes with source-lines=2923 ledger-rows=2923 malformed-json=18 exact-duplicates=28 repairs=0.
result: pass
source: automated
coverage_id: D4
requirement: PIPE-04

### 12. Immutable supplied-file inventory and output-root guard. [01-03 D1]
expected: `tests/pipeline/test_pipeline_outputs.py#test_integrity_inventory_is_sorted_and_rejects_supplied_output_roots` passes.
result: pass
source: automated
coverage_id: D1
requirement: RPRO-02

### 13. Deterministic per-line quality ledger with normalization provenance. [01-03 D2]
expected: `tests/pipeline/test_pipeline_outputs.py#test_full_run_conservation_reconciles_all_lines_and_keeps_rejects_out_of_parquet` passes.
result: pass
source: automated
coverage_id: D2
requirement: PIPE-04

### 14. Reconciled analytical boundary and byte-identical fresh-root reruns. [01-03 D3]
expected: `tests/pipeline/test_pipeline_outputs.py#test_full_run_is_deterministic_across_fresh_roots_and_integrity_command_reports_totals` passes.
result: pass
source: automated
coverage_id: D3
requirement: PIPE-05

### 15. Fixed-schema typed Parquet plus reviewer-readable schema rationale. [01-03 D4]
expected: `tests/pipeline/test_pipeline_outputs.py#test_atomic_writers_emit_fixed_schema_and_stable_bytes` passes.
result: pass
source: automated
coverage_id: D4
requirement: PIPE-06

### 16. Deterministic highest-ERROR service result generated from checked-in static SQL over cleaned Parquet. [01-04 D1]
expected: `tests/pipeline/test_analysis.py#test_service_error_counts_uses_static_sql_and_returns_deterministic_answer` passes; `python -m pipeline analyze --analysis-id service-error-counts --output-root data` runs.
result: pass
source: automated
coverage_id: D1
requirement: PIPE-07

### 17. Seven UTC daily ERROR counts with a strict two-times-median descriptive flag and reconciled service contributions. [01-04 D2]
expected: `tests/pipeline/test_analysis.py#test_daily_error_counts_uses_seven_utc_dates_and_cleaned_error_rows` and `#test_daily_error_counts_applies_only_the_strict_descriptive_median_rule` pass.
result: pass
source: automated
coverage_id: D2
requirement: PIPE-08

### 18. Fixed analysis registry and parameter-bound static SQL evidence contracts. [01-04 D3]
expected: `tests/pipeline/test_analysis.py#test_service_error_counts_registry_declares_all_final_contracts` and `#test_analysis_registry_rejects_an_explicit_unimplemented_query` pass.
result: pass
source: automated
coverage_id: D3
requirement: PIPE-11

### 19. Deterministic top-three normalized ERROR-type ranking with service contributions and visible unclassified count. [01-05 D1]
expected: `tests/pipeline/test_analysis.py#test_top_normalized_errors_ranks_primary_types_and_retains_service_evidence` and `#test_top_normalized_errors_has_deterministic_tie_boundary_and_error_only_filter` pass.
result: pass
source: automated
coverage_id: D1
requirement: PIPE-09

### 20. Ledger issue occurrences and final-action record totals, including explicit zero repairs and both conservation equations. [01-05 D2]
expected: `tests/pipeline/test_analysis.py#test_quality_reconciliation_separates_actions_issues_and_conservation` and `#test_quality_reconciliation_committed_evidence_is_stable_and_complete` pass.
result: pass
source: automated
coverage_id: D2
requirement: PIPE-10

### 21. One no-ID command regenerates all four static SQL evidence tables byte-stably. [01-05 D3]
expected: `python -m pipeline analyze --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data` regenerates all four tables byte-stably.
result: pass
source: automated
coverage_id: D3
requirement: PIPE-11

### 22. Deterministic run manifest and evidence-only Markdown report for all four customer answers. [01-06 D1]
expected: `tests/pipeline/test_evidence.py` and `make verify-phase1` pass; report is evidence-only with manifest-backed numbers.
result: pass
source: automated
coverage_id: D1
requirement: PIPE-11

### 23. Canonical locked reviewer workflow with independently runnable stages and constrained output cleanup. [01-06 D2]
expected: `tests/pipeline/test_end_to_end.py#test_all_regenerates_deterministic_evidence_without_mutating_inputs` and `make verify-phase1` pass.
result: pass
source: automated
coverage_id: D2
requirement: RPRO-01

### 24. Source immutability, deterministic evidence regeneration, and manifest consistency checks. [01-06 D3]
expected: `make verify-phase1` passes all three checks.
result: pass
source: automated
coverage_id: D3
requirement: RPRO-02

### 25. Live supplied-input inventory must match both source and run manifest inventories. [01-07 D1]
expected: `tests/pipeline/test_evidence.py#source_inventory` regressions and `make verify-phase1` pass.
result: pass
source: automated
coverage_id: D1
requirement: RPRO-02

### 26. Phase 1 roadmap goal uses canonical MVP user-story grammar without scope drift. [01-07 D2]
expected: `gsd-tools user-story validate` passes.
result: pass
source: automated
coverage_id: D2

## Summary

total: 26
passed: 26
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
