---
id: 260811-uyg
title: "Fix Phase 01 verification gaps"
status: complete
completed: 2026-08-11T16:06:04Z
commits:
  - 32e5a7b fix(01): verify evidence against a canonical reconstruction and trace through the production path
  - f7855c2 fix(01): strict UTF-8 and JSON parsing and preserve every ISO 8601 offset form
verification: ".planning/phases/01-auditable-log-pipeline-analysis/01-VERIFICATION.md"
---

# Summary: Fix Phase 01 Verification Gaps

Closed all 7 gaps recorded in the Phase 01 verification report
(`01-VERIFICATION.md`, previously `gaps_found`, 22/30 truths) — including both
integrity BLOCKERs. Executed inline (no typed subagents available in this
environment) with atomic, green commits per work unit.

## What changed

**Gap 1 (BLOCKER) — symlink containment**
- `pipeline/integrity.py`: added `authorize_output_path()` which resolves every
  final write/cleanup target and rejects it with `SourceIntegrityError` when it
  escapes the resolved output root (covers symlinked ancestors and symlinked
  final artifacts).
- Applied to every production writer/unlinker: `cmd_run`, `cmd_validate`,
  `cmd_trace`, `clean_generated_outputs`, `run_analysis`, `render_report`,
  `build_run_manifest`.
- Regressions: `evidence/` and `processed/` symlinks aimed at `docs/onboard`
  and at outside directories fail closed for both `run` and clean, leaving
  supplied bytes and outside files untouched.

**Gaps 2 + 7 (BLOCKER) — source-grounded verification**
- New `pipeline/reconstruct.py`: `reconstruct_evidence()` is the single
  production validation/normalization stream (previously duplicated in
  `__main__`), now shared by run, validate, trace, and verification.
- `verify_run_manifest` reconstructs the expected ledger bytes and Parquet
  bytes from `CANONICAL_LOG_INPUT` and requires the live files to match
  byte-for-byte before run_id comparison, so a self-consistent forged set can
  no longer be rebuilt and accepted.
- Adversarial regressions: same-count forged ledger `raw_line` and same-count
  forged Parquet value both fail verification after a manifest rebuild.

**Gap 3 — trace parity**
- Deleted the divergent `parse_and_normalize` tracer. `cmd_trace` now selects
  the traced line from `reconstruct_evidence` and writes production
  `LedgerEntry`/`CleanRecord` artifacts; a parity test proves the trace ledger
  entry and Parquet row equal the full-pipeline rows for the same source line.

**Gap 4 — duplicate provenance**
- Only ACCEPT/REPAIR rows are stored in the digest map; rejected first
  occurrences are never cross-referenced as retained (regression test with two
  identical invalid rows).

**Gap 5 — strict UTF-8/JSON**
- Strict UTF-8 decode with a byte-safe rejected-row representation (valid
  U+FFFD accepted, invalid bytes → `TEXT_INVALID_UTF8`); `parse_constant` hook
  rejects NaN/Infinity as `JSON_MALFORMED`; all evidence serialization uses
  `allow_nan=False`.

**Gap 6 — offset preservation**
- `normalize_timestamp()` extracts the raw offset from a grammar preserving
  `Z`, `+07:00`, `+0700`, and `+07` verbatim; compact and hour-only regressions
  added.

## Evidence

- Full suite: **70 passed** (`pytest -q`), up from 60 with 10 new regressions.
- `ruff check .` and `ruff format --check --exclude .planning .` pass;
  `compileall -q pipeline` passes.
- `make phase1` regenerated `data/evidence/` (ledger now records
  `retained_source_line: null` for rejected rows); `pipeline verify
  --output-root data` passes with the reconstruction check.
- `git diff --exit-code -- docs/onboard` passes — supplied sources unchanged.

## Status

`01-VERIFICATION.md` re-verified: **30/30 truths verified**. The last
behavior-unverified truth — clean-checkout `uv sync --locked` plus the
documented trace command without an existing `.venv` — is proven by
`make clean-checkout-verify`, which builds a fresh Docker container from the
committed tree (`git archive HEAD`), installs uv, and passes the locked sync
and trace commands with all four trace artifacts. No hosted CI was added;
Docker is only an optional local verification harness, in line with the
STACK.md avoidable-complexity guidance.
