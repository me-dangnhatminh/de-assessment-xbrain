---
id: 260811-uyg
title: "Fix Phase 01 verification gaps"
status: in_progress
created: 2026-08-11T14:00:00Z
scope: "pipeline/ + tests/pipeline/ + regenerated data/evidence evidence"
source: ".planning/phases/01-auditable-log-pipeline-analysis/01-VERIFICATION.md"
gaps: 7
blockers: 2
---

# Fix Phase 01 Verification Gaps

Close all 7 gaps recorded in the Phase 01 verification report
(`01-VERIFICATION.md`, status `gaps_found`, 22/30 truths) with adversarial
regression tests, re-run the full verification suite, and refresh the evidence
snapshot. Work is executed inline (no typed subagents available in this
environment) with one atomic commit per task.

## Task 1 — Symlink containment (Gap 1, BLOCKER)

- `pipeline/integrity.py`: add `authorize_output_path(output_root, target)`
  that resolves the final target (`resolve(strict=False)`) and rejects it with
  `SourceIntegrityError` when it escapes the resolved output root — covering
  symlinked ancestors and symlinked final artifacts.
- Authorize every write/cleanup target before opening or unlinking:
  `cmd_run`, `cmd_validate`, `cmd_trace`, `clean_generated_outputs` in
  `pipeline/__main__.py`; `run_analysis` in `pipeline/analysis.py`;
  `render_report` in `pipeline/report.py`; `build_run_manifest` in
  `pipeline/manifest.py`.
- Regression tests: `evidence/` and `processed/` symlinks aimed at
  `docs/onboard` and at an outside directory must fail closed for both
  `pipeline run` and `clean_generated_outputs`, leaving supplied bytes and the
  outside directory untouched.

## Task 2 — Source-grounded verification (Gaps 2 + 7, BLOCKER)

- New `pipeline/reconstruct.py`: `reconstruct_evidence(input_path,
  max_line_bytes) -> (ledger_entries, clean_records)` — the single production
  validation/normalization stream (moved from `_run_validation_stream`).
- `verify_run_manifest` (after `_verify_row_counts`): reconstruct the expected
  ledger bytes and Parquet bytes from `CANONICAL_LOG_INPUT` and require them to
  match the live files byte-for-byte, so a self-consistent forged set can no
  longer be rebuilt and accepted.
- Adversarial tests: modify ledger `raw_line` only (counts unchanged) and
  modify one Parquet value (count unchanged); each must fail verification even
  after a manifest rebuild.

## Task 3 — Validation/normalization/trace parity (Gaps 3, 4, 5, 6)

- Gap 4: only store accepted/repaired rows in the duplicate digest map;
  rejected rows get `retained_source_line = None` and no `EXACT_DUPLICATE`.
- Gap 5: strict UTF-8 decode with a byte-safe rejected-row representation
  (valid U+FFFD accepted); reject `NaN`/`Infinity` via a `parse_constant` hook;
  serialize all evidence with `allow_nan=False`.
- Gap 6: extract the raw offset with a grammar that preserves every accepted
  ISO 8601 form (`Z`, `+07:00`, `+0700`, `+07`).
- Gap 3: rewrite `cmd_trace` to run the traced line through the production
  `reconstruct_evidence` path and production writers; delete the divergent
  `parse_and_normalize` tracer; update the trace contract tests and add a
  trace-vs-full-pipeline parity test.

## Verification (after all tasks)

1. `make phase1` (regenerates `data/evidence/` with the corrected ledger).
2. `make verify-phase1` — ruff check/format, pytest, `pipeline verify`,
   `git diff --exit-code -- docs/onboard`.
3. Update `01-VERIFICATION.md` (status `verified`, all gaps closed), write
   `260811-uyg-SUMMARY.md`, add the STATE.md quick-task row, commit per task.
