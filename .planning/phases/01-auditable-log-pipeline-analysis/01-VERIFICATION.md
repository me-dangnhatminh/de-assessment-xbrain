---
phase: 01-auditable-log-pipeline-analysis
verified: 2026-08-11T16:59:48Z
status: passed
score: 30/30 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: "verified (non-canonical token from prior report; content supported passing; this run re-emits status: passed)"
  previous_score: 30/30
  gaps_closed:
    - "Descendant output-root symlinks can escape the approved root and reach supplied inputs; every write and cleanup target is now resolved and authorized, and evidence/processed symlink regressions fail closed."
    - "A self-consistent forged ledger/Parquet/analysis set could be rebuilt and accepted; verification now reconstructs ledger and Parquet bytes from CANONICAL_LOG_INPUT and compares them byte-for-byte."
    - "Trace used a divergent parse_and_normalize path; cmd_trace now emits the exact production row through the shared reconstruct_evidence stream, with a trace-to-full-pipeline parity test."
    - "The digest map stored the first parsed row before its final action; only ACCEPT/REPAIR rows are now retained as duplicate cross-reference targets."
    - "Replacement decoding misjudged UTF-8 and json.loads accepted NaN/Infinity; strict decoding, a rejecting parse_constant hook, and allow_nan=False serialization are wired and tested."
    - "normalize_timestamp() corrupted compact/hour-only offsets; offset provenance is extracted from a grammar preserving Z, +07:00, +0700, and +07."
    - "The final expected manifest/run_id was rebuilt from the forged output set; the verifier now requires live ledger/Parquet bytes to match a canonical-input reconstruction before run_id comparison."
    - "Clean-checkout locked sync and trace were not exercised without an existing .venv; make clean-checkout-verify now proves them in a fresh Docker container built from the committed tree."
  regressions: []
  gaps_remaining: []
gaps: []
---

# Phase 1: Auditable Log Pipeline & Analysis Verification Report

**Phase Goal:** As a reviewer, I want to run the complete log pipeline and customer analysis, so that I can defend every result from immutable source evidence.
**Verified:** 2026-08-11T16:59:48Z
**Status:** passed
**Re-verification:** Yes — re-run against the live codebase on 2026-08-11. The prior report's `status: verified` token was non-canonical; this run re-verified all 30 truths live and rewrites the token to the canonical `passed`. All 7 previously closed gaps and the Docker clean-checkout proof still hold; no regressions observed.

## User Flow Coverage

User story: «As a reviewer, I want to run the complete log pipeline and customer analysis, so that I can defend every result from immutable source evidence.»

| User-story step | Expected outcome | Codebase evidence | Status |
| --- | --- | --- | --- |
| Create locked environment | `uv sync --locked` works without relying on a prior environment | `make clean-checkout-verify` built a fresh Docker container from `git archive HEAD` (no `.venv`, no uv cache) and passed `uv sync --locked` (duckdb==1.5.5, pytest==9.1.1, ruff==0.16.2) and `uv lock --check` | ✓ VERIFIED |
| Run complete pipeline and analyses | Ledger, Parquet, four tables, report, and manifest are generated and verified | `make phase1` completed in-place (byte-identical regeneration: `git diff --exit-code -- data` is empty); `pipeline verify --output-root data` printed `run manifest verified` | ✓ VERIFIED |
| Trace and inspect quality decisions | Each physical line has stable ledger provenance and dispositions | `cmd_trace` runs the traced line through the production `reconstruct_evidence` stream; live `pipeline trace --source-line 1` wrote all four trace artifacts; ledger carries issues, actions, retained lines | ✓ VERIFIED |
| Defend immutable, source-grounded results | No run can damage source and verify proves derivation from supplied bytes | `authorize_output_path()` rejects symlink escapes before any write; verifier reconstructs ledger/Parquet from `CANONICAL_LOG_INPUT`; `git diff --exit-code -- docs/onboard` passes | ✓ VERIFIED |
| Outcome: "defend every result from immutable source evidence" | Every reported number is reproducible from checked-in SQL over source-derived Parquet with a direct evidence chain | Four tables are byte-stable and regeneration-verified; report cites SQL/result/hash/count/manifest ID per answer; forged ledger/Parquet/inventory/input all fail verification | ✓ VERIFIED |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Clean checkout ingestion preserves all supplied files. | ✓ VERIFIED | `authorize_output_path()` (pipeline/integrity.py:69) resolves every write/cleanup target; `evidence/` and `processed/` symlink regressions fail closed; `make clean-checkout-verify` passed in a fresh container. |
| 2 | Every input line is ledgered with stable validation/disposition evidence. | ✓ VERIFIED | Live ledger has 2,923 JSONL records; source-order tests (`validate_streams_real_source_into_one_ordered_ledger_record_per_line`) pass. |
| 3 | Canonical normal runs produce deterministic, row-conserving Parquet. | ✓ VERIFIED | Direct DuckDB `COUNT(*)` = 2,839; ledger derives 2,839 ACCEPT + 0 REPAIR + 84 REJECT; both conservation equations true. |
| 4 | Four checked-in analyses answer the customer questions without manual arithmetic. | ✓ VERIFIED | Static SQL registry (`ANALYSIS_SPECS`), four CSVs, and report-only CSV readers are wired; `make phase1` regenerated all four tables byte-identically. |
| 5 | Trace follows the production evidence path. | ✓ VERIFIED | `cmd_trace` selects the line from `reconstruct_evidence`; parity test `trace_emits_exactly_the_full_pipeline_row_for_the_same_source_line` passes. |
| 6 | A clean checkout can synchronize uv.lock and invoke trace. | ✓ VERIFIED | `make clean-checkout-verify` re-run today: fresh Docker container from `git archive HEAD`, `uv sync --locked`, `uv lock --check`, and the documented trace command all passed with four trace artifacts. |
| 7 | Trace output is stable and source hash is unchanged. | ✓ VERIFIED | `test_trace_is_stable_across_fresh_output_roots` and source-hash assertions pass in the 70-test suite. |
| 8 | Duplicates cite the first retained line. | ✓ VERIFIED | `reconstruct.py` stores a digest target only for ACCEPT/REPAIR rows; `invalid_duplicate_rows_are_never_cross_referenced_as_retained` regression passes. |
| 9 | ACCEPT/REPAIR/REJECT precedence preserves independent issues. | ✓ VERIFIED | `choose_final_action()` implements reject > repair > accept (pipeline/validation.py:116); `all_issues_are_retained_and_reject_overrides_repair` passes. |
| 10 | JSON/type/timestamp/level/content rules are sound and stable. | ✓ VERIFIED | Strict UTF-8 decode accepts valid U+FFFD and rejects invalid bytes; `parse_constant` rejects NaN/Infinity; evidence serializes with `allow_nan=False`; all three regressions pass. |
| 11 | Known levels are enforced without a service allowlist. | ✓ VERIFIED | `ALLOWED_LEVELS = {INFO, WARN, ERROR}`; validation has no service allowlist; `unknown_service_is_valid_trace_id_is_optional_and_extra_fields_are_visible` passes. |
| 12 | Accepted offset timestamps preserve raw offset text. | ✓ VERIFIED | `_OFFSET_SUFFIX` grammar preserves `Z`, `+07:00`, `+0700`, and `+07`; `normalize_timestamp_preserves_compact_and_hour_only_offsets` passes. |
| 13 | ERROR-only taxonomy and unclassified errors are preserved. | ✓ VERIFIED | `normalize_error()` branches on ERROR and returns `UNCLASSIFIED_ERROR`; unclassified count 35 visible in table 03 and report. |
| 14 | Only analytical actions reach the fixed-schema Parquet. | ✓ VERIFIED | `reconstruct_evidence()` appends clean rows only for ACCEPT/REPAIR; live counts reconcile (2839 = 2839 + 0). |
| 15 | Repeated canonical runs cannot change supplied bytes. | ✓ VERIFIED | `git diff --exit-code -- docs/onboard` passes after `make phase1`; source inventory 14 files hashed before/after. |
| 16 | Static SQL reads Parquet for highest-service/daily results. | ✓ VERIFIED | `pipeline/sql/01` and `02` read `read_parquet(?)` with bound paths; table 01 and 02 CSVs live. |
| 17 | Highest-service ordering is deterministic. | ✓ VERIFIED | SQL orders `error_count DESC, service ASC`; live first answer is payment-api/139; table 01 reconciles 5 service rows to 287 cleaned ERROR rows. |
| 18 | Daily heuristic uses UTC, strict >2× median, ratio, and non-causal wording. | ✓ VERIFIED | SQL 02 emits seven UTC dates, `is_unusual_by_2x_median_rule`, `error_count_to_median_ratio`; only 2026-07-30 (140) flagged; report wording is descriptive, no causation claim. |
| 19 | Top normalized ERROR ranking retains contributions and unclassified rows. | ✓ VERIFIED | SQL 03 ranks CONNECTION_TIMEOUT/HTTP_502/NULL_POINTER with service contributions and unclassified count 35 on every row. |
| 20 | Quality SQL separates issue occurrences/actions and reconciles both equations. | ✓ VERIFIED | SQL 04 emits record totals (incl. explicit REPAIR=0), issue occurrences, and two `is_reconciled=True` conservation rows; committed CSV present. |
| 21 | One no-ID command regenerates all four analyses. | ✓ VERIFIED | `run_all_analyses()` iterates the fixed registry; `make phase1` regenerated all four tables and `git diff -- data` stayed empty. |
| 22 | Canonical Make workflow and stages are runnable. | ✓ VERIFIED | `make phase1` and the `make verify-phase1` component gates (lock presence, Ruff check, Ruff format, pytest, docs diff) each passed on this run. |
| 23 | Report contains four qualified, evidence-linked answers. | ✓ VERIFIED | `render_report()` reads generated CSV/manifest evidence only; report links analysis ID, SQL, result, dataset hash, row counts. |
| 24 | Snapshot verification proves evidence is source-grounded. | ✓ VERIFIED | `_verify_reconstructed_evidence()` reconstructs ledger/Parquet bytes from `CANONICAL_LOG_INPUT`; forged raw-line and Parquet-value regressions fail with named messages. |
| 25 | Report/manifest consume generated evidence rather than calculate answers. | ✓ VERIFIED | `render_report()` parses CSV and manifest only; no Parquet query or aggregate in report.py. |
| 26 | Verification freshly checks supplied inventory. | ✓ VERIFIED | `_verify_source_inventory()` compares a live `inventory_supplied_inputs()` to both persisted layers (source_manifest and run_manifest). |
| 27 | Rebuilt manifest rejects forged source inventory. | ✓ VERIFIED | `test_manifest_verification_rejects_forged_source_inventory_after_rebuild` and three-way-equality test pass. |
| 28 | MVP roadmap goal is a valid user story. | ✓ VERIFIED | `gsd-tools user-story validate` returned `true` with reviewer/capability/outcome slots. |
| 29 | Plan 07 targeted integrity check preserves supplied source. | ✓ VERIFIED | Canonical `pipeline verify` and `git diff --exit-code -- docs/onboard` pass; foreign-input and forged-hash regressions pass. |
| 30 | Plan 08 binds canonical input and independently measures counts. | ✓ VERIFIED | `require_canonical_log_input`, `_verify_input_binding`, `_parquet_row_count` (DuckDB COUNT), and `_ledger_action_counts` are substantive and tested. |

**Score:** 30/30 truths verified. **behavior_unverified:** 0.

### Required Artifacts

| Artifact set | Status | Details |
| --- | --- | --- |
| `pipeline/{ingest,validation,models,normalize}.py` | ✓ VERIFIED | Production flow substantive and wired; UTF-8/JSON, duplicate, and offset edge cases have passing regressions. |
| `pipeline/{integrity,write_outputs}.py` | ✓ VERIFIED | `authorize_output_path()` protects every descendant write/cleanup; writers fail closed on non-finite JSON (`allow_nan=False`). |
| `pipeline/{analysis,sql/*.sql,report}.py` | ✓ VERIFIED | Static queries flow from live Parquet/ledger to deterministic CSVs and report; Python is orchestration only. |
| `pipeline/{reconstruct,manifest}.py` and run manifest | ✓ VERIFIED | Single production stream; verification compares live ledger/Parquet bytes against a canonical-input reconstruction. |
| Ledger, Parquet, schema, four CSVs, report | ✓ PRESENT | Regenerated by `make phase1`; `pipeline verify --output-root data` passes; regeneration is byte-identical (`git diff -- data` empty). |
| `pyproject.toml`, `uv.lock`, Makefile, README | ✓ VERIFIED | Locked sync proven in a fresh Docker container (duckdb==1.5.5, pytest==9.1.1, ruff==0.16.2); `uv lock --check` passes; Make targets and README commands documented. |

All 35 plan-declared artifacts pass existence/substance/wiring checks. The two former trust-boundary failures remain fail-closed with regression coverage.

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `cmd_run`/`cmd_all` | canonical JSONL | `require_canonical_log_input()` | ✓ WIRED | Foreign same-byte repository-local JSONL is rejected before cleanup/publication (test passes). |
| `verify_run_manifest` | live supplied inventory/input hash | `_verify_source_inventory()` + `_verify_input_binding()` | ✓ WIRED | Three-way equality among live bytes, source manifest, and run manifest; descriptor path/hash authenticated. |
| output artifact paths | resolved output root | `authorize_output_path()` before every open/unlink | ✓ WIRED | `evidence/` and `processed/` symlink escapes fail closed (3 tests). |
| verifier | canonical ledger/Parquet reconstruction | `_verify_reconstructed_evidence()` | ✓ WIRED | Reconstructs from `CANONICAL_LOG_INPUT` and compares bytes; same-count forgery fails. |
| manifest builder/verifier | Parquet | DuckDB `COUNT(*)` + byte reconstruction | ✓ WIRED | Count and content are both authenticated; falsified source Parquet count fails after rebuild. |
| verifier | ledger | strict final-action counting + byte reconstruction | ✓ WIRED | Parses each JSONL action, rejects malformed rows, and compares full serialized rows. |
| report | four tables/run manifest | CSV/JSON readers | ✓ WIRED | No report-side aggregate calculation. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Status |
| --- | --- | --- | --- |
| Cleaned Parquet | `clean_records` | Canonical JSONL → validation → normalization → DuckDB | ✓ FLOWING |
| Four result CSVs | query rows | Checked-in SQL over Parquet/ledger | ✓ FLOWING |
| Reviewer report | table/manifest data | Generated CSV and JSON readers | ✓ FLOWING |
| Input identity | descriptor/hash/inventory | Live canonical supplied file | ✓ FLOWING |
| Whole evidence provenance | ledger/Parquet values | `reconstruct_evidence(CANONICAL_LOG_INPUT)` compared at verification | ✓ FLOWING |

### Behavioral Spot-Checks (this run)

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Full test suite | `.venv/bin/python -m pytest -q` | 70 passed (6m43s) | ✓ PASS |
| Lint | `.venv/bin/python -m ruff check .` | All checks passed | ✓ PASS |
| Format | `.venv/bin/python -m ruff format --check --exclude .planning .` | 34 files already formatted | ✓ PASS |
| Compilation | `.venv/bin/python -m compileall -q pipeline` | OK | ✓ PASS |
| Canonical regeneration | `make phase1` | `run manifest verified`; accept=2839 repair=0 reject=84 unclassified_errors=35; `git diff -- data` empty (byte-identical) | ✓ PASS |
| Standalone verification | `.venv/bin/python -m pipeline verify --input .../app_logs_7days.jsonl --output-root data` | `run manifest verified` | ✓ PASS |
| Supplied tree unchanged | `git diff --exit-code -- docs/onboard` | Exit 0 | ✓ PASS |
| Clean-checkout locked sync + trace | `make clean-checkout-verify` (fresh Docker container from `git archive HEAD`) | `uv sync --locked` installed exact locked versions; `uv lock --check` passed; trace wrote all four artifacts | ✓ PASS |
| Trace command | `.venv/bin/python -m pipeline trace --source-line 1 --output-root /tmp/...` | ledger, trace.parquet, trace_manifest.json, tables CSV all written | ✓ PASS |
| User-story validity | `node gsd-tools.cjs user-story validate --story "$STORY"` | role/capability/outcome slots extracted | ✓ PASS |
| Forged evidence defense | `test_manifest_verification_rejects_forged_ledger_raw_line_after_rebuild`, `..._rejects_forged_parquet_value_after_rebuild` | Both fail closed with named `reconstructed ...` messages (in 70-test suite) | ✓ PASS |
| Symlink containment | `run_rejects_symlinked_evidence_dir_aimed_at_supplied_tree`, `clean_generated_outputs_rejects_symlink_escape` | Exit non-zero; no file outside root touched (in 70-test suite) | ✓ PASS |
| UTF-8/strict JSON | `valid_utf8_snowman_is_accepted_but_invalid_utf8_bytes_are_rejected`, `non_standard_json_constants_are_rejected_as_malformed` | U+FFFD ACCEPT; invalid bytes reject; NaN/Infinity malformed (in 70-test suite) | ✓ PASS |
| Offset preservation | `normalize_timestamp_preserves_compact_and_hour_only_offsets` | `+0700`/`+07`/`-07:00`/`Z` preserved verbatim (in 70-test suite) | ✓ PASS |
| Duplicate provenance | `invalid_duplicate_rows_are_never_cross_referenced_as_retained` | Rejected rows never cross-referenced (in 70-test suite) | ✓ PASS |
| Trace parity | `trace_emits_exactly_the_full_pipeline_row_for_the_same_source_line` | Trace ledger/Parquet row byte-equal to full pipeline row (in 70-test suite) | ✓ PASS |

### Probe Execution

SKIPPED — no phase-declared or conventional `scripts/*/tests/probe-*.sh` probe scripts exist. (The `scripts/verify-clean-checkout.sh` harness is executed as a real behavioral check above.)

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| RPRO-01 | 01-01, 01-06 | Locked clean-checkout environment and commands | ✓ SATISFIED | `make clean-checkout-verify` re-run: fresh Docker container, `uv sync --locked`, `uv lock --check`, documented trace command all pass. |
| RPRO-02 | 01-01, 01-03, 01-06–01-08 | Supplied inputs unchanged through recorded hashes | ✓ SATISFIED | Symlink escape rejected before writes; verifier reconstructs ledger/Parquet from canonical log; `git diff -- docs/onboard` empty. |
| PIPE-01 | 01-01, 01-02 | Provenance-preserving physical-line ingestion | ✓ SATISFIED | `iter_source_lines()` envelopes each line before parsing with strict UTF-8 validity; 2,923 ledger rows. |
| PIPE-02 | 01-02 | Stable issue detection | ✓ SATISFIED | `ISSUE_POLICIES` catalogue; JSON/type/timestamp/level/content/unexpected-field regressions pass. |
| PIPE-03 | 01-02 | Explicit accept/repair/reject rules | ✓ SATISFIED | `choose_final_action()` precedence + policy rationales; REPAIR branch exists with honest zero count. |
| PIPE-04 | 01-02, 01-03 | Per-record quality ledger | ✓ SATISFIED | One JSONL record per physical line with source line, issues, action, rationale, normalizations. |
| PIPE-05 | 01-01, 01-03, 01-06, 01-08 | Row conservation and deterministic reruns | ✓ SATISFIED | Both conservation equations reconciled live; fresh-root/byte-identical regeneration proven. |
| PIPE-06 | 01-01, 01-03, 01-06 | Typed Parquet and schema rationale | ✓ SATISFIED | 16-column fixed schema, `schema.json` with rationale, DuckDB queryable. |
| PIPE-07 | 01-04, 01-06 | Highest-ERROR service analysis | ✓ SATISFIED | Static SQL 01 + table 01; payment-api/139 deterministic first row. |
| PIPE-08 | 01-04, 01-06 | Daily pattern and qualified unusual-day rule | ✓ SATISFIED | Static SQL 02; UTC seven dates; strict >2× median; ratio; descriptive wording. |
| PIPE-09 | 01-05, 01-06 | Top normalized error analysis | ✓ SATISFIED | Static SQL 03 + table 03; semantic ranking with contributions and visible unclassified count. |
| PIPE-10 | 01-05, 01-06 | Rejected/repaired quality reconciliation | ✓ SATISFIED | Static SQL 04 separates issue occurrences from record totals, explicit REPAIR=0, both conservation checks true. |
| PIPE-11 | 01-01, 01-04–01-06 | Direct dataset/SQL/result/manifest evidence chain | ✓ SATISFIED | Every report answer cites analysis ID, SQL path, result path, dataset hash, row counts; forged replacement/rebuild fails. |

No orphaned requirements: all 13 Phase 1 requirement IDs are claimed by plans and satisfied.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `pipeline/ingest.py` | `parse_json_line()` | `JSON_NOT_OBJECT` defensive branch (valid JSON that is not an object) has no dedicated unit test | ℹ️ INFO | Canonical source contains no such lines; the branch is present and wired but unexercised. Not a must-have, not a blocker. Recommend a future one-line test if desired. |

No unreferenced `TBD`, `FIXME`, or `XXX` markers found in Phase 1 code or evidence files (`grep` over `pipeline/` and `tests/pipeline/` returned none). All five previously reported REVIEW.md warnings (WR-01..WR-05) remain resolved by the closed gaps.

### Clean-Checkout Verification (formerly human-required)

`make clean-checkout-verify` re-run on 2026-08-11 (this verification): it builds a fresh Docker container from the committed tree (`git archive HEAD` — no `.venv`, no uv cache, no ambient packages), installs uv 0.12.3, and passes `uv sync --locked` (duckdb==1.5.5, pytest==9.1.1, ruff==0.16.2), `uv lock --check`, and the documented trace command with all four trace artifacts. This proves the last previously behavior-unverified truth (clean-checkout locked sync plus trace) and keeps `behavior_unverified: 0`.

### Gaps Summary

None. All 30 must-have truths re-verified against the live codebase and regenerated evidence on 2026-08-11:

- Full pytest suite: **70 passed**; Ruff check and format check pass; `compileall` passes.
- `make phase1` regenerated the complete evidence snapshot; the run ended with `run manifest verified` and accept=2839 / repair=0 / reject=84 / unclassified=35. `git diff -- data` stayed empty, proving byte-stable deterministic regeneration.
- Standalone `pipeline verify` passed; `git diff --exit-code -- docs/onboard` passed (supplied inputs untouched).
- `make clean-checkout-verify` passed in a fresh Docker container built from the committed tree, proving clean-checkout locked sync and the documented trace command.
- `gsd-tools user-story validate` confirmed the canonical MVP user-story goal.
- All four customer tables and the ledger/Parquet/manifest/schema artifacts are present and internally consistent; forged-ledger, forged-Parquet, forged-inventory, forged-input, and falsified-count regressions all fail closed.

The phase goal — "I can defend every result from immutable source evidence" — is observably true: every reported number is regenerable from checked-in SQL over a canonical-input-derived Parquet, with a direct evidence chain and a fail-closed verifier that rejects self-consistent forged evidence.

---

_Verified: 2026-08-11T16:59:48Z_
_Verifier: the agent (gsd-verifier)_
