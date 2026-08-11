---
phase: 01-auditable-log-pipeline-analysis
verified: 2026-08-11T16:06:04Z
status: verified
score: 29/30 must-haves verified
behavior_unverified: 1
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 22/30
  gaps_closed:
    - "Descendant output-root symlinks can escape the approved root and reach supplied inputs; every write and cleanup target is now resolved and authorized, and evidence/processed symlink regressions fail closed."
    - "A self-consistent forged ledger/Parquet/analysis set could be rebuilt and accepted; verification now reconstructs ledger and Parquet bytes from CANONICAL_LOG_INPUT and compares them byte-for-byte."
    - "Trace used a divergent parse_and_normalize path; cmd_trace now emits the exact production row through the shared reconstruct_evidence stream, with a trace-to-full-pipeline parity test."
    - "The digest map stored the first parsed row before its final action; only ACCEPT/REPAIR rows are now retained as duplicate cross-reference targets."
    - "Replacement decoding misjudged UTF-8 and json.loads accepted NaN/Infinity; strict decoding, a rejecting parse_constant hook, and allow_nan=False serialization are wired and tested."
    - "normalize_timestamp() corrupted compact/hour-only offsets; offset provenance is extracted from a grammar preserving Z, +07:00, +0700, and +07."
    - "The final expected manifest/run_id was rebuilt from the forged output set; the verifier now requires live ledger/Parquet bytes to match a canonical-input reconstruction before run_id comparison."
  regressions: []
  gaps_remaining: []
gaps: []
---

# Phase 1: Auditable Log Pipeline & Analysis Verification Report

**Phase Goal:** As a reviewer, I want to run the complete log pipeline and customer analysis, so that I can defend every result from immutable source evidence.
**Verified:** 2026-08-11T16:06:04Z
**Status:** verified
**Re-verification:** Yes — after quick task 260811-uyg closed all 7 recorded gaps

## User Flow Coverage

| User-story step | Expected outcome | Codebase evidence | Status |
| --- | --- | --- | --- |
| Create locked environment | `uv sync --locked` works without relying on a prior environment | `uv sync --locked --offline` succeeded; clean clone was not exercised | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED |
| Run complete pipeline and analyses | Ledger, Parquet, four tables, report, and manifest are generated | `make phase1` completed; `pipeline verify --output-root data` printed `run manifest verified` | ✓ VERIFIED |
| Trace and inspect quality decisions | Each physical line has stable ledger provenance and dispositions | `cmd_trace` runs the traced line through the production stream; ledger rows carry issues, actions, retained lines | ✓ VERIFIED |
| Defend immutable, source-grounded results | No run can damage source and verify proves derivation from supplied bytes | Symlink escape is rejected before any write; verifier reconstructs ledger/Parquet from the canonical log | ✓ VERIFIED — BLOCKER CLOSED |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Clean checkout ingestion preserves all supplied files. | ✓ VERIFIED | `authorize_output_path()` resolves every write/cleanup target; `evidence/` and `processed/` symlink regressions fail closed without touching `docs/onboard`. |
| 2 | Every input line is ledgered with stable validation/disposition evidence. | ✓ VERIFIED | Current ledger: 2,923 JSONL records; source-order tests and canonical run pass. |
| 3 | Canonical normal runs produce deterministic, row-conserving Parquet. | ✓ VERIFIED | Direct DuckDB count is 2,839; ledger derives 2,839 ACCEPT + 0 REPAIR + 84 REJECT. |
| 4 | Four checked-in analyses answer the customer questions without manual arithmetic. | ✓ VERIFIED | Static SQL registry, four CSVs, and report-only CSV readers are wired. |
| 5 | Trace follows the production evidence path. | ✓ VERIFIED | `cmd_trace` selects the line from `reconstruct_evidence`; parity test proves trace ledger/Parquet rows equal full-pipeline rows. |
| 6 | A clean checkout can synchronize uv.lock and invoke trace. | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Existing-checkout `uv sync --locked --offline` passed; no no-`.venv` clone test. |
| 7 | Trace output is stable and source hash is unchanged. | ✓ VERIFIED | `test_trace_is_stable_across_fresh_output_roots` and source-hash assertions pass in suite evidence. |
| 8 | Duplicates cite the first retained line. | ✓ VERIFIED | Only ACCEPT/REPAIR rows are retained; rejected rows are never cross-referenced (regression test added). |
| 9 | ACCEPT/REPAIR/REJECT precedence preserves independent issues. | ✓ VERIFIED | `choose_final_action()` implements reject > repair > accept; focused tests cover it. |
| 10 | JSON/type/timestamp/level/content rules are sound and stable. | ✓ VERIFIED | Strict UTF-8 decode accepts valid U+FFFD and rejects invalid bytes; NaN/Infinity are REJECTed; evidence serializes with `allow_nan=False`. |
| 11 | Known levels are enforced without a service allowlist. | ✓ VERIFIED | `ALLOWED_LEVELS`; validation has no service allowlist. |
| 12 | Accepted offset timestamps preserve raw offset text. | ✓ VERIFIED | Offset grammar preserves `Z`, `+07:00`, `+0700`, and `+07`; compact and hour-only regressions pass. |
| 13 | ERROR-only taxonomy and unclassified errors are preserved. | ✓ VERIFIED | `normalize_error()` branches on ERROR and returns `UNCLASSIFIED_ERROR`. |
| 14 | Only analytical actions reach the fixed-schema Parquet. | ✓ VERIFIED | `reconstruct_evidence()` appends clean rows only for ACCEPT/REPAIR; live counts reconcile. |
| 15 | Repeated canonical runs cannot change supplied bytes. | ✓ VERIFIED | Descendant symlinks are authorized before open/unlink; `git diff --exit-code -- docs/onboard` passes after `make phase1`. |
| 16 | Static SQL reads Parquet for highest-service/daily results. | ✓ VERIFIED | Registered parameter-bound DuckDB queries and CSV outputs are present and live. |
| 17 | Highest-service ordering is deterministic. | ✓ VERIFIED | SQL orders `error_count DESC, service ASC`; current first answer is payment-api/139. |
| 18 | Daily heuristic uses UTC, strict >2× median, ratio, and non-causal wording. | ✓ VERIFIED | SQL, CSV, report, and tests agree. |
| 19 | Top normalized ERROR ranking retains contributions and unclassified rows. | ✓ VERIFIED | SQL 03, CSV, and ranking tests are substantive/wired. |
| 20 | Quality SQL separates issue occurrences/actions and reconciles both equations. | ✓ VERIFIED | SQL 04 reads ledger/Parquet and includes zero REPAIR. |
| 21 | One no-ID command regenerates all four analyses. | ✓ VERIFIED | `run_all_analyses()` iterates the fixed registry. |
| 22 | Canonical Make workflow and stages are runnable. | ✓ VERIFIED | `make phase1` and `make verify-phase1` dispatch the same documented commands. |
| 23 | Report contains four qualified, evidence-linked answers. | ✓ VERIFIED | `render_report()` reads generated CSV/manifest evidence; report links all required artifacts. |
| 24 | Snapshot verification proves evidence is source-grounded. | ✓ VERIFIED | `verify_run_manifest` reconstructs ledger/Parquet bytes from `CANONICAL_LOG_INPUT`; forged same-count changes fail. |
| 25 | Report/manifest consume generated evidence rather than calculate answers. | ✓ VERIFIED | Report parses CSV and manifest only; it does not query Parquet. |
| 26 | Verification freshly checks supplied inventory. | ✓ VERIFIED | `_verify_source_inventory()` compares a live inventory to both persisted layers. |
| 27 | Rebuilt manifest rejects forged source inventory. | ✓ VERIFIED | Dedicated adversarial test and live comparison are wired. |
| 28 | MVP roadmap goal is a valid user story. | ✓ VERIFIED | `user-story.validate --pick valid` returned `true`. |
| 29 | Plan 07 targeted integrity check preserves supplied source. | ✓ VERIFIED | Canonical `pipeline verify` and `git diff --exit-code -- docs/onboard` passed. |
| 30 | Plan 08 binds canonical input and independently measures counts. | ✓ VERIFIED | `require_canonical_log_input`, `_verify_input_binding`, `_parquet_row_count`, and `_ledger_action_counts` are substantive and tested. |

**Score:** 29/30 truths verified (1 present, behavior-unverified).

### Required Artifacts

| Artifact set | Status | Details |
| --- | --- | --- |
| `pipeline/{ingest,validation,models,normalize}.py` | ✓ VERIFIED | Production flow is substantive/wired; UTF-8/JSON, duplicate, and offset edge cases now have passing regressions. |
| `pipeline/{integrity,write_outputs}.py` | ✓ VERIFIED | `authorize_output_path()` protects every descendant write and cleanup; writers fail closed on non-finite JSON. |
| `pipeline/{analysis,sql/*.sql,report}.py` | ✓ VERIFIED | Static queries flow from live Parquet/ledger to deterministic CSVs and report. |
| `pipeline/{reconstruct,manifest}.py` and run manifest | ✓ VERIFIED | One production stream; verification compares live ledger/Parquet bytes against a canonical-input reconstruction. |
| Ledger, Parquet, schema, four CSVs, report | ✓ PRESENT | Regenerated by `make phase1`; `pipeline verify --output-root data` passes with the reconstruction check. |
| `pyproject.toml`, `uv.lock`, Makefile, README | ⚠️ PRESENT | Locked sync, lint, formatting, and module compile pass; fresh-clone behavior remains unobserved. |

All 35 plan-declared artifacts pass the GSD existence/substance checker, and both former trust-boundary failures are now fail-closed with regression coverage.

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `cmd_run`/`cmd_all` | canonical JSONL | `require_canonical_log_input()` | ✓ WIRED | Foreign same-byte repository file is rejected before cleanup/publication. |
| `verify_run_manifest` | live supplied inventory/input hash | inventory and descriptor checks | ✓ WIRED | Correctly verifies canonical membership/hash. |
| output artifact paths | resolved output root | `authorize_output_path()` before every open/unlink | ✓ WIRED | `evidence/` and `processed/` symlink escapes fail closed. |
| verifier | canonical ledger/Parquet reconstruction | `_verify_reconstructed_evidence()` | ✓ WIRED | Reconstructs from `CANONICAL_LOG_INPUT` and compares bytes; same-count forgery fails. |
| manifest builder/verifier | Parquet | DuckDB `COUNT(*)` + byte reconstruction | ✓ WIRED | Count and content are both authenticated. |
| verifier | ledger | strict final-action counting + byte reconstruction | ✓ WIRED | Parses each JSONL action and compares full serialized rows. |
| report | four tables/run manifest | CSV/JSON readers | ✓ WIRED | No report-side aggregate calculation. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Status |
| --- | --- | --- | --- |
| Cleaned Parquet | `clean_records` | Canonical JSONL → validation → normalization → DuckDB | ✓ FLOWING |
| Four result CSVs | query rows | Checked-in SQL over Parquet/ledger | ✓ FLOWING |
| Reviewer report | table/manifest data | Generated CSV and JSON readers | ✓ FLOWING |
| Input identity | descriptor/hash/inventory | Live canonical supplied file | ✓ FLOWING |
| Whole evidence provenance | ledger/Parquet values | `reconstruct_evidence(CANONICAL_LOG_INPUT)` compared at verification | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Locked dependency sync | `uv sync --locked --offline` | Resolved/checked packages in this checkout | ✓ PASS |
| Code quality | `ruff check .` and `ruff format --check --exclude .planning .` | Both passed | ✓ PASS |
| Compilation | `python -m compileall -q pipeline` | Passed | ✓ PASS |
| Canonical evidence verification | `make phase1` then `pipeline verify --output-root data` | `run manifest verified` | ✓ PASS |
| Supplied tree unchanged | `git diff --exit-code -- docs/onboard` | Passed | ✓ PASS |
| Symlink containment | `evidence -> docs/onboard` and `processed -> outside`, then `pipeline run`/clean | Exit non-zero; no file written or unlinked outside the root | ✓ PASS |
| Forged evidence defense | Modify ledger `raw_line` only or one Parquet value, rebuild manifest, then verify | `reconstructed quality ledger/Parquet does not match canonical input derivation` | ✓ PASS |
| UTF-8/strict JSON | Valid U+FFFD and invalid bytes; `NaN`/`Infinity` inputs | U+FFFD ACCEPT; invalid bytes TEXT_INVALID_UTF8; constants JSON_MALFORMED | ✓ PASS |
| Offset preservation | `normalize_timestamp(+0700 / +07 / -07:00)` | Raw offsets preserved verbatim | ✓ PASS |
| Duplicate provenance | Two identical invalid rows through `pipeline validate` | Both REJECT; neither cross-references a rejected line | ✓ PASS |
| Trace parity | `pipeline trace` line 1 vs full `pipeline run` | Ledger entry and Parquet row byte-for-byte equal | ✓ PASS |

### Probe Execution

SKIPPED — no phase-declared or conventional probe scripts exist.

### Requirements Coverage

| Requirement | Status | Evidence |
| --- | --- | --- |
| RPRO-01 | ? NEEDS HUMAN | Locked sync works here; clean clone without `.venv` not exercised. |
| RPRO-02 | ✓ SATISFIED | Symlink escape rejected before writes; verifier proves ledger/Parquet derive from the canonical log. |
| PIPE-01 | ✓ SATISFIED | Bounded physical-line iterator retains provenance with strict UTF-8 validity. |
| PIPE-02 | ✓ SATISFIED | Non-standard JSON constants are rejected; UTF-8 validity is judged by strict decoding. |
| PIPE-03 | ✓ SATISFIED | Duplicate policy cites the first retained (ACCEPT/REPAIR) source line only. |
| PIPE-04 | ✓ SATISFIED | Per-record ledger has source line, issues, action, rationale, and normalizations. |
| PIPE-05 | ✓ SATISFIED | Source immutability and source-derived evidence are fail-closed. |
| PIPE-06 | ✓ SATISFIED | Typed live-queryable Parquet and schema rationale exist. |
| PIPE-07 | ✓ SATISFIED | Static service-count SQL and result exist. |
| PIPE-08 | ✓ SATISFIED | UTC daily analysis and qualified rule exist. |
| PIPE-09 | ✓ SATISFIED | Top normalized error SQL and service contributions exist. |
| PIPE-10 | ✓ SATISFIED | Reconciliation distinguishes issue/action units and totals. |
| PIPE-11 | ✓ SATISFIED | A reviewer can trace every reported result to canonical-derived evidence; forged replacement/rebuild fails. |

### Anti-Patterns Resolved

| File | Line | Pattern | Status | Resolution |
| --- | --- | --- | --- | --- |
| `pipeline/integrity.py` | `authorize_output_path()` | Root-only output authorization | 🛑 RESOLVED | Final target resolved and compared against the approved root before open/unlink. |
| `pipeline/__main__.py` | `cmd_run`/`clean_generated_outputs` | Unchecked descendant writes/cleanup | 🛑 RESOLVED | Every target authorized; symlink regressions added. |
| `pipeline/manifest.py` | `_verify_reconstructed_evidence()` | Count-only/self-referential verification | 🛑 RESOLVED | Live ledger/Parquet bytes must equal a canonical reconstruction. |
| `pipeline/__main__.py` | `cmd_trace` | Trace implements a divergent pipeline | ⚠️ RESOLVED | Trace emits production rows via `reconstruct_evidence`; parity test added. |
| `pipeline/reconstruct.py` | duplicate retention | Duplicate map populated before disposition | ⚠️ RESOLVED | Only ACCEPT/REPAIR rows stored as retained. |
| `pipeline/ingest.py` | decode/parse hooks | Replacement UTF-8 and permissive JSON constants | ⚠️ RESOLVED | Strict decode + rejecting `parse_constant`; `allow_nan=False` serialization. |
| `pipeline/normalize.py` | `_OFFSET_SUFFIX` | Last-six-character offset extraction | ⚠️ RESOLVED | Grammar preserves every accepted ISO 8601 offset form. |
| `tests/pipeline/test_evidence.py` | — | Temporarily edits tracked SQL | ⚠️ RESOLVED | Kept as-is; runs within pytest temp state and restores in `finally`. |

No unreferenced `TBD`, `FIXME`, or `XXX` markers were found in Phase 1 code/evidence files.

### Human Verification Required After Gap Closure

1. **Clean locked checkout**

   **Test:** Clone fresh with no `.venv`, run `uv sync --locked`, then `uv run --locked python -m pipeline trace --output-root /tmp/trace`.

   **Expected:** Commands succeed without ambient packages or the repository fallback.

   **Why human:** This verifier used an existing checkout; it cannot establish fresh-machine behavior.

### Gaps Summary

Quick task 260811-uyg closed all seven gaps recorded by the previous verification (two integrity blockers). The output-root guard now authorizes every descendant write and cleanup target, so symlinked `evidence/`/`processed/` paths fail closed instead of escaping to supplied inputs. Verification now reconstructs the expected ledger and Parquet bytes from `CANONICAL_LOG_INPUT` with the single production stream (`pipeline/reconstruct.py`) and requires the live files to match, so a self-consistent forged set — including a same-count `raw_line` or Parquet-value change — can no longer be rebuilt and accepted. Trace, duplicate provenance, strict UTF-8/JSON handling, and ISO 8601 offset preservation all reuse or match the production path with dedicated regressions. The full suite passes (70 tests), `make phase1` regenerates byte-stable evidence, `pipeline verify` passes on `data`, and `docs/onboard` remains unchanged. One behavior remains for a human on a fresh machine: a clean-checkout locked sync and trace run without an existing `.venv`.

---

_Verified: 2026-08-11T16:06:04Z_
_Verifier: the agent (gsd-verifier)_
