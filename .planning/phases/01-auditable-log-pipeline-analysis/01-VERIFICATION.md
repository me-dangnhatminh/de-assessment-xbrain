---
phase: 01-auditable-log-pipeline-analysis
verified: 2026-08-11T04:39:18Z
status: gaps_found
score: 21/25 must-haves verified
behavior_unverified: 2
overrides_applied: 0
gaps:
  - truth: "From a clean checkout, a reviewer can verify hashes for every supplied input and run ingestion without any source file being changed."
    status: failed
    reason: "The standalone manifest verifier trusts the saved source_inventory; it never inventories docs/onboard again or compares live SHA-256 values to that record."
    artifacts:
      - path: "pipeline/manifest.py"
        issue: "verify_run_manifest() verifies source_manifest.json as an artifact, but has no call to inventory_supplied_inputs() and no live-inventory comparison."
      - path: "tests/pipeline/test_evidence.py"
        issue: "Tamper tests cover result, SQL, counts, and links, but not a falsified or stale source inventory."
    missing:
      - "During verification, recompute the complete supplied-input inventory and fail when it differs from source_manifest.json / run_manifest.json."
      - "Add a regression test that proves a forged or stale source inventory is rejected."
  - truth: "The committed evidence snapshot regenerates without source changes and passes hash or internal-consistency verification for Parquet, ledger, schema, source manifest, four tables, report, and run manifest per D-17."
    status: failed
    reason: "The snapshot verifier can accept a regenerated manifest built from a falsified source inventory, so its source-integrity claim is not internally complete."
    artifacts:
      - path: "pipeline/manifest.py"
        issue: "The run_id is rebuilt from the persisted source inventory rather than an independently re-hashed live inventory."
    missing:
      - "Bind D-17 verification to a fresh, complete source inventory comparison before accepting the run manifest."
behavior_unverified_items:
  - truth: "A clean-checkout reviewer can synchronize exactly the dependency versions recorded in uv.lock and invoke the tracer through the documented module command."
    test: "In a fresh clone with a globally installed uv, run `uv sync --locked`, then `uv run --locked python -m pipeline trace --output-root /tmp/trace`."
    expected: "Dependency synchronization and the trace command complete without using a pre-existing .venv."
    why_human: "The verification host has no uv executable; make uses its documented existing-.venv fallback, and no test creates a clean environment."
  - truth: "One canonical make phase1 command performs locked synchronization, source-integrity checks, full pipeline generation, all four analyses, report generation, and verification; every stage also remains independently runnable per D-14."
    test: "In a fresh clone with globally installed uv, run `make phase1`, then each documented stage command."
    expected: "The canonical command uses the locked uv path and every stage succeeds independently."
    why_human: "This host ran the .venv fallback because uv is unavailable; the existing test checks command declarations rather than a clean uv-backed execution."
---

# Phase 1: Auditable Log Pipeline & Analysis Verification Report

**Phase Goal:** A reviewer can run and defend the complete log-quality and customer-analysis workflow from immutable source lines to recorded results.
**Verified:** 2026-08-11T04:39:18Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## MVP Mode Contract

**BLOCKER:** ROADMAP.md marks this phase `Mode: mvp`, but its Goal is not a valid user story. The canonical validator returned `false` for the roadmap goal; it is missing the required `As a …, I want to …, so that … .` form. Therefore formal MVP user-flow verification cannot be authoritative until the roadmap goal is corrected (for example through `/gsd mvp-phase 1`). The technical audit below was still performed against the four roadmap success criteria and plan must-haves to make this escalation actionable.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Clean checkout verifies every supplied-input hash and ingestion does not change a source file. | ✗ FAILED | `verify_run_manifest()` does not rehash the live `docs/onboard` inventory; adversarial isolated run accepted a forged inventory. |
| 2 | Every line reaches stable validation/disposition in a provenance ledger. | ✓ VERIFIED | `cmd_run` streams `SourceEnvelope` records, writes 2,923 ordered ledger rows, and `make verify-phase1` passed. |
| 3 | Reruns yield row-conserving deterministic Parquet with schema/rationale. | ✓ VERIFIED | `cmd_run`, deterministic atomic writers, conservation checks, and `test_all_regenerates_deterministic_evidence_without_mutating_inputs`. |
| 4 | Four checked-in analyses and recorded evidence answer the customer questions without manual arithmetic. | ✓ VERIFIED | Static SQL registry, four CSVs, evidence-only report, and successful canonical run. |
| 5 | One real source line traces through hash, provenance, validation, normalization, Parquet, SQL, and manifest. | ✓ VERIFIED | `cmd_trace` and the three behavioral tracer tests exercise the whole path. |
| 6 | Locked clean-checkout tracer command is runnable. | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `uv.lock`, README, and CLI exist; host lacks `uv`, so clean-environment execution was not observed. |
| 7 | Repeated trace executions are stable and preserve input hash. | ✓ VERIFIED | `test_trace_is_stable_across_fresh_output_roots` plus source diff check. |
| 8 | Every physical line, including malformed JSON and later duplicates, is retained in ordered validation evidence. | ✓ VERIFIED | `iter_source_lines`, duplicate provenance logic, and `test_validate_streams_real_source...`. |
| 9 | ACCEPT/REPAIR/REJECT precedence and all independent issues are visible. | ✓ VERIFIED | `choose_final_action` enforces reject > repair > accept; unit test covers conflicting actions. |
| 10 | Required/type/timestamp/level/content/extra-field rules have stable policies. | ✓ VERIFIED | `ISSUE_POLICIES`, `validate_record`, and dedicated validation tests. |
| 11 | Known levels are enforced while unknown non-empty services remain valid. | ✓ VERIFIED | `ALLOWED_LEVELS` and `test_unknown_service_is_valid...`. |
| 12 | Aware timestamp conversion preserves raw representation and derives UTC independently of repair. | ✓ VERIFIED | `normalize_timestamp` plus offset-equivalence test. |
| 13 | Only ERROR rows receive taxonomy; unmatched errors remain visible and INFO/WARN taxonomy is null. | ✓ VERIFIED | `normalize_error` and ERROR/non-ERROR normalization tests. |
| 14 | Only analytical actions reach fixed-schema Parquet, while ledger conservation holds. | ✓ VERIFIED | `cmd_run` conservation guard; full-run test queries emitted Parquet. |
| 15 | Canonical output artifacts are byte-stable while sources remain unchanged during the run. | ✓ VERIFIED | Deterministic writers and clean-root rerun test; this does not repair the separate stale-baseline gap in Truth 1. |
| 16 | Static SQL over cleaned Parquet produces the highest-error service and UTC daily results. | ✓ VERIFIED | Parameter-bound DuckDB SQL `01`/`02`, generated CSVs, and analysis tests. |
| 17 | Highest-service ordering is deterministic. | ✓ VERIFIED | SQL explicitly orders `error_count DESC, service ASC`; result is `payment-api` (139). |
| 18 | Daily heuristic uses the full UTC window, strict >2× median rule, ratio, and non-causal contributions. | ✓ VERIFIED | SQL `02`, result CSV, report wording, and focused daily tests. |
| 19 | Top-three semantic ERROR ranking keeps service evidence and exposes unclassified errors. | ✓ VERIFIED | SQL `03`, tie-boundary test, and committed three-row CSV. |
| 20 | Quality SQL separates issue occurrences from actions and proves both conservation equations. | ✓ VERIFIED | SQL `04`, explicit zero REPAIR row, and reconciliation tests. |
| 21 | No-ID analysis regenerates all four deterministic tables without Python aggregates. | ✓ VERIFIED | `run_all_analyses` only orchestrates static SQL; canonical run produced all four tables. |
| 22 | `make phase1` performs the locked canonical workflow and all stages stay independently runnable. | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Host execution passed through the documented `.venv` fallback; clean uv-backed execution was not observed. |
| 23 | The Markdown report presents four evidence-linked answers and qualified methodology. | ✓ VERIFIED | `render_report` consumes CSV/manifest data and report links each answer to SQL, result, dataset hash, counts, and analysis ID. |
| 24 | Snapshot verification detects all listed artifact and consistency failures. | ✗ FAILED | It detects saved artifact/hash/query tampering, but accepts an altered source inventory once its derived manifest is rebuilt. |
| 25 | Report and manifest consume generated evidence rather than independently calculating answers. | ✓ VERIFIED | `report.py` reads CSV/JSON only; it does not import DuckDB or query Parquet. |

**Score:** 21/25 truths verified (2 present, behavior-unverified)

### Required Artifacts

| Artifact set | Expected | Status | Details |
| --- | --- | --- | --- |
| `pipeline/{ingest,validation,normalize,integrity,write_outputs,models}.py` | Provenance-first pipeline and deterministic output contracts | ✓ VERIFIED | All substantive, imported by `pipeline.__main__`, and exercised by focused tests. |
| `data/processed/logs_clean.parquet`, ledger, schema, source manifest | Generated pipeline evidence | ✓ VERIFIED | Current manifest links them; Parquet has 2,839 rows and ledger 2,923 lines. |
| `pipeline/sql/01`–`04` and four CSVs | Checked-in analysis and recorded results | ✓ VERIFIED | SQL is parameter-bound and CSV schemas match registry contracts. |
| `pipeline/{manifest,report}.py`, report, run manifest | Evidence graph and review surface | ⚠️ HOLLOW INTEGRITY | Content links work, but source inventory is not compared to live supplied bytes during verify. |
| `Makefile`, `README.md`, CLI | Reviewer workflow | ⚠️ PRESENT, CLEAN-UV UNVERIFIED | Canonical commands and stage wiring exist; only fallback runtime was available here. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| CLI | immutable JSONL | provenance envelopes and before/after inventory | ✓ WIRED | `cmd_run` calls `inventory_supplied_inputs()` around execution. |
| validation | normalization / Parquet | ACCEPT/REPAIR filtering | ✓ WIRED | `_run_validation_stream` only appends clean rows after final disposition. |
| analysis registry | SQL / Parquet / CSV | parameter binding and atomic CSV write | ✓ WIRED | `run_analysis` validates input files, executes SQL with `?` values, then writes schema-checked CSV. |
| report | result tables / manifest | CSV/JSON readers | ✓ WIRED | `render_report` reads all four tables and analysis IDs; no aggregate query path. |
| verifier | live supplied inputs | integrity comparison | ✗ NOT WIRED | `verify_run_manifest` never calls `inventory_supplied_inputs()`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| Cleaned Parquet | `clean_records` | source JSONL → validation → normalization | DuckDB-written 2,839-row Parquet | ✓ FLOWING |
| Four CSV tables | query rows | static SQL over Parquet / ledger | DuckDB results, not hardcoded literals | ✓ FLOWING |
| Reviewer report | CSV rows + manifest analyses | generated evidence paths | Direct table values and linked metadata | ✓ FLOWING |
| Source-integrity verdict | `source_inventory` | saved `source_manifest.json` only | No fresh live comparison | ✗ DISCONNECTED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Canonical workflow, lint, tests, source diff | `make verify-phase1` | Exit 0; Ruff passed; 44 tests passed; `docs/onboard` diff clean | ✓ PASS |
| Current linked-evidence verification | `.venv/bin/python -m pipeline verify --input … --output-root data` | `run manifest verified` | ✓ PASS |
| Source-inventory fail-closed property | Isolated output: forge `source_manifest.source_inventory`, rebuild run manifest, call `verify_run_manifest()` | Verification accepted forged inventory (`VERIFY_ACCEPTED_FALSIFIED_SOURCE_INVENTORY`) | ✗ FAIL |

### Probe Execution

SKIPPED — no phase-declared or conventional `scripts/**/tests/probe-*.sh` probes exist.

### Requirements Coverage

| Requirement | Source Plan(s) | Status | Evidence |
| --- | --- | --- | --- |
| RPRO-01 | 01, 06 | ? NEEDS HUMAN | Lock file, docs, and commands exist; no clean `uv sync --locked` execution was possible on this host. |
| RPRO-02 | 01, 03, 06 | ✗ BLOCKED | Live source inventory is not checked during standalone manifest verification. |
| PIPE-01 | 01, 02 | ✓ SATISFIED | Bounded physical-line iterator retains source-line provenance. |
| PIPE-02 | 02 | ✓ SATISFIED | Stable parser and validation issue codes are covered by focused tests. |
| PIPE-03 | 02 | ✓ SATISFIED | `ISSUE_POLICIES` and final-action precedence make accept/repair/reject explicit. |
| PIPE-04 | 02, 03 | ✓ SATISFIED | Per-line JSONL ledger contains provenance, issues, actions, and normalizations. |
| PIPE-05 | 01, 03, 06 | ✓ SATISFIED | Conservation checks and deterministic clean-root rerun tests pass. |
| PIPE-06 | 01, 03, 06 | ✓ SATISFIED | Fixed schema/rationale and typed Parquet are emitted and queried. |
| PIPE-07 | 04, 06 | ✓ SATISFIED | Static highest-service SQL and committed result table. |
| PIPE-08 | 04, 06 | ✓ SATISFIED | UTC daily SQL records ratio, strict heuristic, and contributions. |
| PIPE-09 | 05, 06 | ✓ SATISFIED | Top-three normalized ERROR SQL and deterministic tie test. |
| PIPE-10 | 05, 06 | ✓ SATISFIED | Quality reconciliation retains action and issue-occurrence counting units. |
| PIPE-11 | 01, 04, 05, 06 | ✓ SATISFIED | Report/manifest chain ties each answer to SQL, result, dataset hash, and counts. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `pipeline/manifest.py` | 224–243 | Verification trusts persisted source inventory | 🛑 Blocker | A forged/stale inventory can be represented as verified evidence. |
| `ROADMAP.md` | Phase 1 goal | MVP mode with non-user-story goal | 🛑 Blocker | The mandated MVP verification flow cannot be applied authoritatively. |

No unreferenced `TBD`, `FIXME`, or `XXX` debt markers were found in Phase 1 implementation or evidence files. `return None` occurrences are parser/control-flow behavior, not output stubs.

### Gaps Summary

The pipeline, SQL, ledger, Parquet, and reviewer report are substantive and wired; the final verification gate also exits successfully. That success is insufficient for the source-integrity contract: a manifest rebuilt from a falsified source inventory passes because verification rehashes only files named by the saved manifest and never recomputes the immutable source inventory.

This is one root-cause implementation gap affecting roadmap criterion 1, D-17 snapshot assurance, and RPRO-02. Independently, the phase is configured as MVP but lacks a valid user-story goal, which is an escalation-gate planning discrepancy rather than an application-code defect.

---

_Verified: 2026-08-11T04:39:18Z_
_Verifier: the agent (gsd-verifier)_
