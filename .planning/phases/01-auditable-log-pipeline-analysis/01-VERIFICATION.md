---
phase: 01-auditable-log-pipeline-analysis
verified: 2026-08-11T12:34:34Z
status: gaps_found
score: 22/30 must-haves verified
behavior_unverified: 1
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 20/25
  gaps_closed:
    - "Production run/all now reject a foreign repository-local JSONL before cleanup or publication."
    - "Verification authenticates the canonical input descriptor and remeasures Parquet/ledger action counts."
  gaps_remaining: []
  regressions:
    - "Descendant output-root symlinks can escape the approved root and can reach supplied inputs."
    - "A self-consistent forged ledger/Parquet/analysis set can be rebuilt and accepted without derivation from the canonical input."
gaps:
  - truth: "From a clean checkout, a reviewer can run ingestion without any supplied source file being changed."
    status: failed
    reason: "The output-root guard authorizes only the root; writers and cleanup follow descendant symlinks after that check."
    artifacts:
      - path: "pipeline/integrity.py"
        issue: "validate_output_root() does not authorize final artifact paths or reject symlinked ancestors."
      - path: "pipeline/__main__.py"
        issue: "cmd_run() and clean_generated_outputs() write/unlink descendant paths directly."
    missing:
      - "Authorize every write and cleanup target against the resolved output root and reject symlinked ancestors before opening or unlinking."
      - "Add regression coverage for evidence/ and processed/ symlinks aimed at docs/onboard."
  - truth: "A reviewer can defend every recorded result as derived from immutable canonical source evidence."
    status: failed
    reason: "verify_run_manifest() checks counts and self-rebuilt hashes but never reconstructs/compares ledger or Parquet content with the canonical log."
    artifacts:
      - path: "pipeline/manifest.py"
        issue: "_verify_row_counts() accepts a forged same-count ledger; build_run_manifest() then creates a matching self-referential run_id."
    missing:
      - "Reconstruct or independently validate canonical ledger and Parquet content during verification, then compare provenance, actions, normalized rows, analyses, and hashes."
      - "Add an adversarial test that changes raw_line or a Parquet value without changing counts and requires verification failure."
  - truth: "The tracer proves a real source line through the same production validation and normalization evidence path."
    status: failed
    reason: "trace uses parse_and_normalize(), a separate implementation with different issue, action, digest, taxonomy, and normalization schemas."
    artifacts:
      - path: "pipeline/__main__.py"
        issue: "cmd_trace()/parse_and_normalize() do not reuse validate_record(), choose_final_action(), normalize_error(), or production LedgerEntry/CleanRecord serialization."
    missing:
      - "Reuse the production path or explicitly narrow trace's contract and test parity against the full pipeline row."
  - truth: "Exact duplicates cross-reference the first retained source line."
    status: failed
    reason: "The digest map records the first parsed row before its final action; a second invalid duplicate cites a rejected line as retained."
    artifacts:
      - path: "pipeline/__main__.py"
        issue: "cmd_validate() and _run_validation_stream() call setdefault before choose_final_action()."
    missing:
      - "Only store accepted/repaired rows as retained, or rename the field/policy to first observed and update documentation."
  - truth: "JSONL validation accurately distinguishes invalid UTF-8 and standard JSON input."
    status: failed
    reason: "Replacement decoding rejects valid U+FFFD data, while json.loads accepts NaN/Infinity and classifies them as acceptable unexpected fields."
    artifacts:
      - path: "pipeline/ingest.py"
        issue: "errors='replace' plus U+FFFD detection is not a UTF-8 validity check, and parsing has no rejecting parse_constant hook."
    missing:
      - "Strictly decode UTF-8 with a byte-safe invalid-row representation, reject non-standard JSON constants, and serialize evidence with allow_nan=False."
  - truth: "Valid timestamp offsets preserve their raw representation."
    status: failed
    reason: "normalize_timestamp() takes the last six characters; valid +0700 becomes 0+0700 and +07 becomes :00+07."
    artifacts:
      - path: "pipeline/normalize.py"
        issue: "Offset extraction assumes only Z or ±HH:MM syntax."
    missing:
      - "Extract the offset from a grammar/match that preserves all accepted ISO 8601 forms, with compact and hour-only regressions."
  - truth: "The committed evidence snapshot's verification establishes source-grounded integrity, not merely internal consistency."
    status: failed
    reason: "A modified ledger raw_line with unchanged action totals, followed by manifest rebuild, passes verify_run_manifest()."
    artifacts:
      - path: "pipeline/manifest.py"
        issue: "The final expected manifest/run_id is rebuilt from the forged current output set."
    missing:
      - "Bind evidence content to a deterministic reconstruction from CANONICAL_LOG_INPUT or equivalent independently authenticated canonical digests."
behavior_unverified_items:
  - truth: "A clean-checkout reviewer can synchronize exactly uv.lock and invoke the documented module command."
    test: "In a fresh clone with no .venv, run uv sync --locked and uv run --locked python -m pipeline trace --output-root /tmp/trace."
    expected: "Dependency synchronization and the tracer complete solely through the locked environment."
    why_human: "uv sync --locked --offline passed in this existing checkout, but a fresh-clone/no-.venv execution was not performed."
---

# Phase 1: Auditable Log Pipeline & Analysis Verification Report

**Phase Goal:** As a reviewer, I want to run the complete log pipeline and customer analysis, so that I can defend every result from immutable source evidence.
**Verified:** 2026-08-11T12:34:34Z
**Status:** gaps_found
**Re-verification:** Yes — after Plan 01-08 gap closure

## User Flow Coverage

| User-story step | Expected outcome | Codebase evidence | Status |
| --- | --- | --- | --- |
| Create locked environment | `uv sync --locked` works without relying on a prior environment | `uv sync --locked --offline` succeeded; clean clone was not exercised | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED |
| Run complete pipeline and analyses | Ledger, Parquet, four tables, report, and manifest are generated | A temporary `all --clean` run completed and current `pipeline verify` passed | ✓ VERIFIED |
| Trace and inspect quality decisions | Each physical line has stable ledger provenance and dispositions | Current ledger has 2,923 rows; however duplicate-retention semantics are false for invalid duplicates | ✗ FAILED |
| Defend immutable, source-grounded results | No run can damage source and verify proves derivation from supplied bytes | Descendant symlink escape and self-consistent forged-ledger acceptance reproduced | ✗ FAILED — BLOCKER |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Clean checkout ingestion preserves all supplied files. | ✗ FAILED | Descendant output symlink is accepted; source guard is root-only. |
| 2 | Every input line is ledgered with stable validation/disposition evidence. | ✓ VERIFIED | Current ledger: 2,923 JSONL records; source-order tests and canonical run pass. |
| 3 | Canonical normal runs produce deterministic, row-conserving Parquet. | ✓ VERIFIED | Direct DuckDB count is 2,839; ledger derives 2,839 ACCEPT + 0 REPAIR + 84 REJECT. |
| 4 | Four checked-in analyses answer the customer questions without manual arithmetic. | ✓ VERIFIED | Static SQL registry, four CSVs, and report-only CSV readers are wired. |
| 5 | Trace follows the production evidence path. | ✗ FAILED | Separate tracer contracts disagree with production taxonomy/action/digest behavior. |
| 6 | A clean checkout can synchronize uv.lock and invoke trace. | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Existing-checkout `uv sync --locked --offline` passed; no no-.venv clone test. |
| 7 | Trace output is stable and source hash is unchanged. | ✓ VERIFIED | `test_trace_is_stable_across_fresh_output_roots` and source-hash assertions exist and pass in suite evidence. |
| 8 | Duplicates cite the first retained line. | ✗ FAILED | Two identical invalid rows yield line 2 `retained_source_line=1`, even though line 1 is REJECT. |
| 9 | ACCEPT/REPAIR/REJECT precedence preserves independent issues. | ✓ VERIFIED | `choose_final_action()` implements reject > repair > accept; focused tests cover it. |
| 10 | JSON/type/timestamp/level/content rules are sound and stable. | ✗ FAILED | Valid U+FFFD is rejected as invalid UTF-8; NaN is accepted as an unexpected field. |
| 11 | Known levels are enforced without a service allowlist. | ✓ VERIFIED | `ALLOWED_LEVELS`; validation has no service allowlist. |
| 12 | Accepted offset timestamps preserve raw offset text. | ✗ FAILED | `+0700 → 0+0700` and `+07 → :00+07`. |
| 13 | ERROR-only taxonomy and unclassified errors are preserved. | ✓ VERIFIED | `normalize_error()` branches on ERROR and returns `UNCLASSIFIED_ERROR`. |
| 14 | Only analytical actions reach the fixed-schema Parquet. | ✓ VERIFIED | `_run_validation_stream()` appends clean rows only for ACCEPT/REPAIR; live counts reconcile. |
| 15 | Repeated canonical runs cannot change supplied bytes. | ✗ FAILED | Symlinked descendant writes can reach supplied files before post-write inventory detects it. |
| 16 | Static SQL reads Parquet for highest-service/daily results. | ✓ VERIFIED | Registered parameter-bound DuckDB queries and CSV outputs are present and live. |
| 17 | Highest-service ordering is deterministic. | ✓ VERIFIED | SQL orders `error_count DESC, service ASC`; current first answer is payment-api/139. |
| 18 | Daily heuristic uses UTC, strict >2× median, ratio, and non-causal wording. | ✓ VERIFIED | SQL, CSV, report, and tests agree. |
| 19 | Top normalized ERROR ranking retains contributions and unclassified rows. | ✓ VERIFIED | SQL 03, CSV, and ranking tests are substantive/wired. |
| 20 | Quality SQL separates issue occurrences/actions and reconciles both equations. | ✓ VERIFIED | SQL 04 reads ledger/Parquet and includes zero REPAIR. |
| 21 | One no-ID command regenerates all four analyses. | ✓ VERIFIED | `run_all_analyses()` iterates the fixed registry. |
| 22 | Canonical Make workflow and stages are runnable. | ✓ VERIFIED | `uv sync --locked --offline` and a temporary `all --clean` run passed; Makefile dispatches the same commands. |
| 23 | Report contains four qualified, evidence-linked answers. | ✓ VERIFIED | `render_report()` reads generated CSV/manifest evidence; report links all required artifacts. |
| 24 | Snapshot verification proves evidence is source-grounded. | ✗ FAILED | Same-count forged ledger plus rebuilt manifest was accepted. |
| 25 | Report/manifest consume generated evidence rather than calculate answers. | ✓ VERIFIED | Report parses CSV and manifest only; it does not query Parquet. |
| 26 | Verification freshly checks supplied inventory. | ✓ VERIFIED | `_verify_source_inventory()` compares a live inventory to both persisted layers. |
| 27 | Rebuilt manifest rejects forged source inventory. | ✓ VERIFIED | Dedicated adversarial test and live comparison are wired. |
| 28 | MVP roadmap goal is a valid user story. | ✓ VERIFIED | `user-story.validate --pick valid` returned `true`. |
| 29 | Plan 07 targeted integrity check preserves supplied source. | ✓ VERIFIED | Canonical `pipeline verify` and `git diff --exit-code -- docs/onboard` passed. |
| 30 | Plan 08 binds canonical input and independently measures counts. | ✓ VERIFIED | `require_canonical_log_input`, `_verify_input_binding`, `_parquet_row_count`, and `_ledger_action_counts` are substantive and tested. |

**Score:** 22/30 truths verified (1 present, behavior-unverified).

### Required Artifacts

| Artifact set | Status | Details |
| --- | --- | --- |
| `pipeline/{ingest,validation,models,normalize}.py` | ⚠️ PARTIAL | Production flow is substantive/wired; duplicate, UTF-8/JSON, and offset edge cases fail. |
| `pipeline/{integrity,write_outputs}.py` | ✗ BLOCKER | Root check does not protect descendant writes or cleanup. |
| `pipeline/{analysis,sql/*.sql,report}.py` | ✓ VERIFIED | Static queries flow from live Parquet/ledger to deterministic CSVs and report. |
| `pipeline/manifest.py` and run manifest | ✗ BLOCKER | Live input/count checks work, but provenance/content derivation is not authenticated. |
| Ledger, Parquet, schema, four CSVs, report | ✓ PRESENT | Current artifacts are substantive and live-counted, but can be replaced with a self-consistent forged set. |
| `pyproject.toml`, `uv.lock`, Makefile, README | ⚠️ PRESENT | Locked sync, lint, formatting, and module compile pass; fresh-clone behavior remains unobserved. |

All 35 plan-declared artifacts pass the GSD existence/substance checker. That result is insufficient for the two integrity blockers above; both are Level-3/4 trust-boundary failures.

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `cmd_run`/`cmd_all` | canonical JSONL | `require_canonical_log_input()` | ✓ WIRED | Foreign same-byte repository file is rejected before cleanup/publication. |
| `verify_run_manifest` | live supplied inventory/input hash | inventory and descriptor checks | ✓ WIRED | Correctly verifies canonical membership/hash. |
| output artifact paths | resolved output root | final path authorization | ✗ NOT WIRED | Descendant symlinks are followed by writers/cleanup. |
| verifier | canonical ledger/Parquet reconstruction | content/provenance comparison | ✗ NOT WIRED | Only action totals/counts and self-rebuilt hashes are compared. |
| manifest builder/verifier | Parquet | DuckDB `COUNT(*)` | ✓ WIRED | `_parquet_row_count()` is called in both paths. |
| verifier | ledger | strict final-action counting | ✓ WIRED | `_ledger_action_counts()` parses each JSONL action. |
| report | four tables/run manifest | CSV/JSON readers | ✓ WIRED | No report-side aggregate calculation. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Status |
| --- | --- | --- | --- |
| Cleaned Parquet | `clean_records` | Canonical JSONL → validation → normalization → DuckDB | ✓ FLOWING |
| Four result CSVs | query rows | Checked-in SQL over Parquet/ledger | ✓ FLOWING |
| Reviewer report | table/manifest data | Generated CSV and JSON readers | ✓ FLOWING |
| Input identity | descriptor/hash/inventory | Live canonical supplied file | ✓ FLOWING |
| Whole evidence provenance | ledger/Parquet values | No reconstruction/comparison to canonical source | ✗ DISCONNECTED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Locked dependency sync | `uv sync --locked --offline` | Resolved/checked 9 packages | ✓ PASS |
| Code quality | `uv run --locked ruff check pipeline tests/pipeline` and format check | Both passed | ✓ PASS |
| Compilation | `uv run --locked python -m compileall -q pipeline` | Passed | ✓ PASS |
| Canonical evidence verification | `python -m pipeline verify ... --output-root data` | `run manifest verified` | ✓ PASS |
| Supplied tree unchanged now | `git diff --exit-code -- docs/onboard` | Passed | ✓ PASS |
| Symlink containment | Temporary output with `evidence -> /tmp/.../outside`, then `pipeline run` | Exit 0; ledger/schema/manifest written outside root | ✗ FAIL |
| Forged evidence defense | Modify ledger `raw_line` only, rebuild manifest, then verify | `FORGED_LEDGER_RESULT ACCEPTED` | ✗ FAIL |
| UTF-8/strict JSON | Temporary valid U+FFFD and `NaN` inputs | U+FFFD ACCEPT; `NaN` ACCEPT/UNEXPECTED_FIELD | ✗ FAIL |
| Offset preservation | `normalize_timestamp(+0700/+07)` | Returned malformed offset strings | ✗ FAIL |

### Probe Execution

SKIPPED — no phase-declared or conventional probe scripts exist.

### Requirements Coverage

| Requirement | Status | Evidence |
| --- | --- | --- |
| RPRO-01 | ? NEEDS HUMAN | Locked sync works here; clean clone without `.venv` not exercised. |
| RPRO-02 | ✗ BLOCKED | Canonical input/hash checks were added, but descendants can mutate supplied files and verifier does not prove derived evidence. |
| PIPE-01 | ✓ SATISFIED | Bounded physical-line iterator retains provenance. |
| PIPE-02 | ✗ BLOCKED | Non-standard JSON constants and UTF-8 handling do not meet a robust JSON-quality contract. |
| PIPE-03 | ✗ BLOCKED | Duplicate policy claims “first retained” but records first observed rejected lines. |
| PIPE-04 | ✓ SATISFIED | Per-record ledger has source line, issues, action, rationale, and normalizations. |
| PIPE-05 | ✗ BLOCKED | Live count checks work, but source immutability and source-derived evidence are not fail-closed. |
| PIPE-06 | ✓ SATISFIED | Typed live-queryable Parquet and schema rationale exist. |
| PIPE-07 | ✓ SATISFIED | Static service-count SQL and result exist. |
| PIPE-08 | ✓ SATISFIED | UTC daily analysis and qualified rule exist. |
| PIPE-09 | ✓ SATISFIED | Top normalized error SQL and service contributions exist. |
| PIPE-10 | ✓ SATISFIED | Reconciliation distinguishes issue/action units and totals. |
| PIPE-11 | ✗ BLOCKED | A reviewer cannot reliably trace a reported result back to canonical-derived evidence after forged replacement/rebuild. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- |
| `pipeline/integrity.py` | 56–66 | Root-only output authorization | 🛑 BLOCKER | Descendant symlink can target immutable supplied material. |
| `pipeline/__main__.py` | 441–479 | Cleanup/writes use unchecked descendant paths | 🛑 BLOCKER | Enables the symlink escape. |
| `pipeline/manifest.py` | 302–419 | Count-only/self-referential verification | 🛑 BLOCKER | Rebuilt forged evidence passes. |
| `pipeline/__main__.py` | 125–295 | Trace implements a divergent pipeline | ⚠️ WARNING | Trace is not a production parity proof. |
| `pipeline/__main__.py` | 309–338, 359–375 | Duplicate map populated before disposition | ⚠️ WARNING | False retained-line provenance. |
| `pipeline/ingest.py` | 52–68, 83–90 | Replacement-based UTF-8 and permissive JSON constants | ⚠️ WARNING | Misclassifies valid input and accepts invalid JSON. |
| `pipeline/normalize.py` | 51 | Last-six-character offset extraction | ⚠️ WARNING | Corrupts accepted raw offsets. |
| `tests/pipeline/test_evidence.py` | 274–286 | Temporarily edits tracked SQL | ⚠️ WARNING | Unsafe under interruption/concurrent tooling. |

No unreferenced `TBD`, `FIXME`, or `XXX` markers were found in Phase 1 code/evidence files.

### Human Verification Required After Gap Closure

1. **Clean locked checkout**

   **Test:** Clone fresh with no `.venv`, run `uv sync --locked`, then `uv run --locked python -m pipeline trace --output-root /tmp/trace`.

   **Expected:** Commands succeed without ambient packages or the repository fallback.

   **Why human:** This verifier used an existing checkout; it cannot establish fresh-machine behavior.

### Gaps Summary

Plan 08 closed the previous, narrower gaps: production input is now constrained to the canonical log, input membership/hash is checked live, Parquet is measured live, and final actions are derived from the ledger. Those fixes do not achieve the phase goal because two broader integrity boundaries remain open: the code can write through a descendant output symlink, and verification can approve a fully replaced evidence graph after its manifest is rebuilt. The ledger/parser/trace warnings additionally make some claimed provenance inaccurate. No later roadmap phase explicitly owns these Phase 1 pipeline integrity defects, so none are deferred.

---

_Verified: 2026-08-11T12:34:34Z_
_Verifier: the agent (gsd-verifier)_
