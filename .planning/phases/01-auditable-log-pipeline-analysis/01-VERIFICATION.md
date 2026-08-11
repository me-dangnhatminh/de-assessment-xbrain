---
phase: 01-auditable-log-pipeline-analysis
verified: 2026-08-11T05:24:21Z
status: gaps_found
score: 20/25 must-haves verified
behavior_unverified: 2
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 21/25
  gaps_closed:
    - "Standalone verification now recomputes the complete live docs/onboard inventory and rejects either persisted source_inventory when it disagrees."
    - "The Phase 1 MVP goal now passes the canonical user-story validator."
  gaps_remaining: []
  regressions: []
gaps:
  - truth: "Recorded Phase 1 evidence is bound to the supplied immutable log input."
    status: failed
    reason: "cmd_run accepts an arbitrary repository-relative --input and verify_run_manifest() only compares docs/onboard inventories; it never validates source_manifest.input.path/hash against a supplied input."
    artifacts:
      - path: "pipeline/__main__.py"
        issue: "cmd_run() resolves and processes any --input without requiring it to be under SUPPLIED_ROOT."
      - path: "pipeline/manifest.py"
        issue: "_verify_source_inventory() authenticates docs/onboard but ignores the persisted input descriptor."
    missing:
      - "Restrict production run/all input to the canonical supplied log, or require it to be inside SUPPLIED_ROOT."
      - "During verification, validate input.path membership and recompute its live SHA-256 against both the source manifest and supplied inventory."
      - "Add a regression that a foreign repository-local JSONL input cannot reach a passing verify result."
  - truth: "Recorded row-conservation evidence proves the actual Parquet row count."
    status: failed
    reason: "The Parquet count is copied from source_manifest.json during manifest construction and never measured from logs_clean.parquet during verification."
    artifacts:
      - path: "pipeline/manifest.py"
        issue: "_manifest_payload() uses row_counts['parquet']; _verify_row_counts() compares two persisted declarations only."
      - path: "tests/pipeline/test_evidence.py"
        issue: "No regression modifies source_manifest row_counts.parquet, rebuilds the run manifest, and requires failure."
    missing:
      - "Query COUNT(*) from the generated Parquet at build and verify time, and require it to equal the declared Parquet count."
      - "Derive or cross-check ACCEPT plus REPAIR and REJECT totals from the ledger during verification."
      - "Add the adversarial rebuilt-count regression."
behavior_unverified_items:
  - truth: "A clean-checkout reviewer can synchronize exactly the dependency versions recorded in uv.lock and invoke the tracer through the documented module command."
    test: "In a fresh clone with globally installed uv, run uv sync --locked, then uv run --locked python -m pipeline trace --output-root /tmp/trace."
    expected: "Locked synchronization and the trace command complete without relying on a pre-existing .venv."
    why_human: "uv is not on this verification host PATH; make deliberately used the existing .venv fallback."
  - truth: "One canonical make phase1 command performs the locked workflow and every documented stage remains independently runnable."
    test: "In a fresh clone with globally installed uv, run make phase1, then each documented stage command."
    expected: "The locked uv path is used and all stages succeed independently."
    why_human: "The canonical command was exercised only through the documented .venv fallback, not in a clean uv-backed environment."
---

# Phase 1: Auditable Log Pipeline & Analysis Verification Report

**Phase Goal:** As a reviewer, I want to run the complete log pipeline and customer analysis, so that I can defend every result from immutable source evidence.
**Verified:** 2026-08-11T05:24:21Z
**Status:** gaps_found
**Re-verification:** Yes — after Plan 01-07 gap closure

## User Flow Coverage

| User-story step | Expected outcome | Codebase evidence | Status |
| --- | --- | --- | --- |
| Reviewer creates the locked environment | `uv sync --locked` works from a clean checkout | `uv.lock`, README commands, and Makefile are present; this host has no `uv` executable | ⚠️ HUMAN NEEDED |
| Reviewer runs the complete pipeline and analysis | Ledger, Parquet, four SQL tables, report, and manifest are generated | `make verify-phase1` exited 0 through the documented `.venv` fallback | ✓ VERIFIED |
| Reviewer traces log-quality decisions | Every physical line is ledgered with stable issues and a final action | `cmd_run()` streams `SourceEnvelope` records; full test gate passed; current ledger has 2,923 lines | ✓ VERIFIED |
| Reviewer defends results as immutable-source and row-conserving | A passing verifier proves the evidence came from supplied bytes and real Parquet totals | Independent adversarial checks accepted a foreign input and a rebuilt forged Parquet count | ✗ FAILED — BLOCKER |

The corrected roadmap Goal passes `gsd-tools ... user-story.validate --pick valid` (`true`). It retains the same Phase 1 requirements and all four success criteria; the MVP metadata blocker in the prior report is closed.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Clean checkout verifies every supplied-input hash and ingestion does not change a source file. | ✗ FAILED | Fresh three-way `docs/onboard` inventory comparison is implemented, but the processed `--input` is not bound to that inventory. A foreign JSONL completed `run → analyze → report → verify` with exit codes `[0, 0, 0, 0]`. |
| 2 | Every line reaches stable validation/disposition in a provenance ledger. | ✓ VERIFIED | `cmd_run()` writes ordered `LedgerEntry` data; committed ledger has 2,923 lines and the full test gate passed. |
| 3 | Reruns yield row-conserving deterministic Parquet with documented schema/rationale. | ✗ FAILED | Normal runs produce 2,839 Parquet rows and deterministic outputs, but the verifier accepts a rebuilt manifest after `row_counts.parquet` is falsified. Thus recorded row-conservation evidence is not independently proven. |
| 4 | Four checked-in analyses and recorded evidence answer customer questions without manual arithmetic. | ✓ VERIFIED | Static SQL registry, four generated CSVs, and evidence-only report completed in the canonical gate. |
| 5 | One real source line traces through hash, provenance, validation, normalization, Parquet, SQL, and manifest evidence. | ✓ VERIFIED | `cmd_trace` is substantive and the tracer tests run in the full suite. |
| 6 | A clean-checkout reviewer can synchronize exact lock versions and invoke the tracer. | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Lockfile, README, and CLI are present, but no clean `uv` execution was possible. |
| 7 | Repeated trace executions are stable and preserve the source hash. | ✓ VERIFIED | Tracer stability/source-integrity tests passed in the complete test gate. |
| 8 | Every physical line, including malformed JSON and duplicates, remains ordered validation evidence. | ✓ VERIFIED | `iter_source_lines`, duplicate provenance, and validation tests are wired through `cmd_run`. |
| 9 | ACCEPT/REPAIR/REJECT precedence and independent issues remain visible. | ✓ VERIFIED | `choose_final_action()` implements REJECT > REPAIR > ACCEPT; focused tests cover conflicts. |
| 10 | Required/type/timestamp/level/content/extra-field rules have stable policies. | ✓ VERIFIED | `ISSUE_POLICIES` and `validate_record()` are substantive and tested. |
| 11 | Known levels are enforced while non-empty unknown services remain valid. | ✓ VERIFIED | `ALLOWED_LEVELS` is enforced without a service allowlist. |
| 12 | Aware timestamps preserve raw values and derive UTC separately from repair. | ✓ VERIFIED | `normalize_timestamp()` retains the raw value and records a normalization. |
| 13 | Only ERROR rows receive taxonomy; unmatched errors remain visible and INFO/WARN taxonomy is null. | ✓ VERIFIED | `normalize_error()` enforces this branch and returns `UNCLASSIFIED_ERROR` for unmatched ERROR rows. |
| 14 | Only analytical actions reach fixed-schema Parquet while ledger conservation holds during execution. | ✓ VERIFIED | `cmd_run()` checks in-memory conservation before writing; a direct query finds 2,839 current Parquet rows. |
| 15 | Canonical artifacts are byte-stable while sources remain unchanged during a run. | ✓ VERIFIED | Atomic deterministic writers and `git diff --exit-code -- docs/onboard` passed. |
| 16 | Static SQL produces highest-error service and UTC daily results. | ✓ VERIFIED | `AnalysisSpec` executes parameter-bound `01` and `02` SQL over Parquet. |
| 17 | Highest-service ordering is deterministic. | ✓ VERIFIED | SQL orders by `error_count DESC, service ASC`; current result leads with `payment-api` at 139. |
| 18 | Daily heuristic uses the UTC window, strict >2× median rule, ratio, and non-causal contributions. | ✓ VERIFIED | SQL `02`, result CSV, report wording, and tests are consistent. |
| 19 | Top-three semantic ERROR ranking retains service evidence and exposes unclassified errors. | ✓ VERIFIED | SQL `03`, its result CSV, and ranking tests are present and exercised. |
| 20 | Quality SQL separates issue occurrences from actions and proves both conservation equations. | ✓ VERIFIED | SQL `04` reads the ledger and Parquet, including an explicit zero-REPAIR row. |
| 21 | The no-ID analysis command regenerates all four deterministic SQL tables. | ✓ VERIFIED | `run_all_analyses()` orchestrates only registered static SQL; the canonical gate regenerated all four. |
| 22 | `make phase1` performs the locked canonical workflow and stages remain independently runnable. | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | The workflow passed through the `.venv` fallback; a fresh `uv`-backed run remains unobserved. |
| 23 | The Markdown report presents four evidence-linked answers and qualified methodology. | ✓ VERIFIED | `render_report()` consumes generated CSV/manifest evidence and contains direct SQL/table/hash links. |
| 24 | Snapshot verification detects all linked-artifact and consistency failures. | ✗ FAILED | It now rejects forged source inventories, but accepts a foreign input and self-consistent forged Parquet count. |
| 25 | Report and manifest consume generated evidence rather than independently calculating answers. | ✓ VERIFIED | `report.py` reads CSV/JSON; it does not query Parquet or calculate customer aggregates. |

**Score:** 20/25 truths verified (2 present, behavior-unverified).

### Required Artifacts

| Artifact set | Expected | Status | Details |
| --- | --- | --- | --- |
| `pipeline/{ingest,validation,normalize,integrity,write_outputs,models}.py` | Provenance-first deterministic pipeline | ✓ VERIFIED | Substantive and wired through the CLI and complete test suite. |
| Ledger, schema, and cleaned Parquet | Dynamic generated evidence | ✓ VERIFIED | Current artifacts contain 2,923 ledger records and 2,839 directly counted Parquet rows. |
| `pipeline/sql/01`–`04` plus four CSVs | Executable analysis and recorded results | ✓ VERIFIED | Static, parameter-bound SQL is wired to DuckDB output. |
| `pipeline/{manifest,report}.py`, run manifest, report | Evidence graph and review surface | ✗ HOLLOW INTEGRITY | The source-input descriptor and actual Parquet count are not independently authenticated. |
| `pyproject.toml`, `uv.lock`, Makefile, README | Clean-reviewer workflow | ⚠️ PRESENT, CLEAN-UV UNVERIFIED | Correct artifacts/commands exist; this host lacks `uv`. |

All 35 plan-declared artifact checks passed at existence/substance level. The plan tool reported 23 of 24 key-link patterns; its Phase 01-07 user-story-regex pattern missed the Markdown emphasis syntax, but the canonical validator independently returned `true`.

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- |
| CLI | supplied JSONL | source envelopes, hashes, and before/after inventory | ⚠️ PARTIAL | Default uses the canonical log, but `cmd_run()` allows an untrusted repository-local input. |
| Manifest verifier | live supplied tree | fresh inventory vs both saved inventories | ✓ WIRED | `_verify_source_inventory()` calls `inventory_supplied_inputs()` and its two adversarial source-inventory tests passed. |
| Source manifest input descriptor | live supplied input | membership/hash validation | ✗ NOT WIRED | No verifier reads `source_manifest['input']`. |
| Source manifest count | actual Parquet | direct count/reconciliation | ✗ NOT WIRED | The verifier compares self-declared metadata, not `COUNT(*) FROM read_parquet(...)`. |
| Analysis registry | SQL, Parquet, and CSVs | bound paths and atomic CSV writes | ✓ WIRED | Four output tables regenerated successfully. |
| Report | result tables and run manifest | CSV/JSON readers only | ✓ WIRED | No independent aggregate path exists in the report renderer. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
| --- | --- | --- | --- | --- |
| Cleaned Parquet | `clean_records` | source JSONL → validation → normalization | DuckDB-written rows | ✓ FLOWING |
| Four result CSVs | query rows | static SQL over Parquet/ledger | DuckDB query results | ✓ FLOWING |
| Reviewer report | table rows + manifest data | generated CSV/JSON | Direct evidence values | ✓ FLOWING |
| Immutable-input assertion | processed-input descriptor | saved `input.path`/hash | Descriptor is never checked against live supplied inventory | ✗ DISCONNECTED |
| Row-conservation assertion | `row_counts.parquet` | saved source manifest count | No Parquet measurement in build or verify | ✗ DISCONNECTED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Full canonical fallback workflow, lint, tests, source diff | `make verify-phase1` | Exit 0; generated evidence, verified manifest, Ruff, pytest, and supplied-tree diff all passed | ✓ PASS |
| Fresh live source-inventory defense | Two named source-inventory tests | `2 passed` | ✓ PASS |
| Canonical MVP goal | `gsd-tools query user-story.validate ... --pick valid` | `true` | ✓ PASS |
| Foreign-input defense | Temporary repository-local copy supplied to `run`, `analyze`, `report`, `verify` | All stage codes were `0`; saved path was outside `docs/onboard` | ✗ FAIL |
| Parquet-count defense | Increment source-manifest count, rebuild run manifest, invoke verifier | `FORGED_PARQUET_COUNT_ACCEPTED` | ✗ FAIL |

### Probe Execution

SKIPPED — no phase-declared or conventional `scripts/**/tests/probe-*.sh` probes exist.

### Requirements Coverage

| Requirement | Source plan(s) | Status | Evidence |
| --- | --- | --- | --- |
| RPRO-01 | 01, 06 | ? NEEDS HUMAN | Lockfile and commands exist, but clean `uv sync --locked` was not observed. |
| RPRO-02 | 01, 03, 06, 07 | ✗ BLOCKED | Fresh supplied-tree inventory is now real, but successful evidence can still derive from a non-supplied input. |
| PIPE-01 | 01, 02 | ✓ SATISFIED | Bounded physical-line iterator preserves source-line provenance. |
| PIPE-02 | 02 | ✓ SATISFIED | Stable parse/validation codes are implemented and tested. |
| PIPE-03 | 02 | ✓ SATISFIED | Explicit policy catalogue and action precedence are wired. |
| PIPE-04 | 02, 03 | ✓ SATISFIED | Per-line JSONL ledger captures provenance, issues, actions, and normalizations. |
| PIPE-05 | 01, 03, 06 | ✗ BLOCKED | Execution checks counts, but reviewer-facing snapshot verification does not prove the actual Parquet count. |
| PIPE-06 | 01, 03, 06 | ✓ SATISFIED | Fixed schema/rationale and typed Parquet are emitted and directly queryable. |
| PIPE-07 | 04, 06 | ✓ SATISFIED | Static highest-service SQL and result table exist. |
| PIPE-08 | 04, 06 | ✓ SATISFIED | UTC daily SQL records ratio, strict heuristic, and contributions. |
| PIPE-09 | 05, 06 | ✓ SATISFIED | Top-normalized-error SQL and deterministic ranking evidence exist. |
| PIPE-10 | 05, 06 | ✓ SATISFIED | Reconciliation distinguishes issue occurrence and final-action counts. |
| PIPE-11 | 01, 04, 05, 06 | ✓ SATISFIED | Report/manifest links answers to SQL, tables, dataset hash, and counts; input-authentication gap remains recorded under RPRO-02. |

### Anti-Patterns and Review Findings

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- |
| `pipeline/__main__.py` | 453–498 | Arbitrary `--input` accepted by production run | 🛑 BLOCKER | A passing evidence graph need not originate from supplied log bytes. |
| `pipeline/manifest.py` | 97–101, 188–197, 245–265 | Parquet count is self-declared and only cross-compared | 🛑 BLOCKER | A self-consistent rebuilt manifest can assert a false row count. |
| `pipeline/ingest.py` | 52–68 | U+FFFD is treated as invalid UTF-8 after replacement decoding | ⚠️ WARNING | A valid literal U+FFFD is falsely rejected; invalid bytes are not losslessly represented. |
| `pipeline/normalize.py` | 47–55 | Last-six-character offset extraction | ⚠️ WARNING | Accepted `+0700` becomes `0+0700`; accepted `+07` becomes `:00+07`. |

The two critical and two warning findings in `01-REVIEW.md` are independently confirmed. The offset cases were executed directly. No unreferenced `TBD`, `FIXME`, or `XXX` markers were found in the Phase 1 implementation/evidence files; empty collections found are normal initialization or parser control flow, not output stubs.

### Human Verification After Gap Closure

1. **Clean locked environment**

   **Test:** In a fresh clone with `uv` installed, run `uv sync --locked` and the documented tracer command.

   **Expected:** Both complete without any existing `.venv`.

   **Why human:** The current host has no `uv` executable.

2. **Clean canonical workflow**

   **Test:** In that same fresh clone, run `make phase1` and each independently documented stage.

   **Expected:** The locked `uv` path is used and all commands succeed.

   **Why human:** The observed run used the intentional fallback, not the clean-checkout path.

### Gaps Summary

Plan 01-07 closed the prior stale-inventory defect: standalone verification now re-hashes the live supplied tree, and the canonical MVP user story is valid. That improvement does not bind the data that the pipeline actually processes to that supplied tree. In addition, manifest verification lets reconstructed metadata authenticate a false Parquet row count. Both are observable integrity failures, not merely missing tests, and prevent this phase from claiming a defensible immutable-source, row-conserving evidence chain.

No later roadmap phase specifically promises to repair RPRO-02 or PIPE-05, so neither blocker is deferred.

---

_Verified: 2026-08-11T05:24:21Z_
_Verifier: the agent (gsd-verifier)_
