# Phase 1 Multi-Source Coverage Audit

**Audited:** 2026-08-11  
**Plan set:** 01-01 through 01-04  
**Result:** All in-scope GOAL, REQ, RESEARCH, and CONTEXT items are covered.

## Source Coverage

| SOURCE | ID | Feature / requirement | Plan | Status | Notes |
|---|---|---|---|---|---|
| GOAL | — | Reviewer can run and defend the complete workflow from immutable source lines to recorded results | 01-01..04 | COVERED | Tracer → full quality path → four analyses → report/canonical verification. |
| REQ | RPRO-01 | Locked clean-checkout environment and verification commands | 01-01, 01-04 | COVERED | Human-approved packages, `uv.lock`, Make/CLI commands, full gate. |
| REQ | RPRO-02 | Recorded hashes prove supplied files unchanged | 01-01, 01-02, 01-04 | COVERED | Tracer hash, complete sorted inventory, pre/post and Git checks. |
| REQ | PIPE-01 | Read every JSONL line with source-line provenance | 01-02 | COVERED | Envelope precedes parsing; one ledger record per physical line. |
| REQ | PIPE-02 | Stable issue codes cover all required quality categories | 01-02 | COVERED | Explicit catalogue, policy map, observed and synthetic tests. |
| REQ | PIPE-03 | Explicit accept/repair/reject rules and rationale | 01-02 | COVERED | Conservative policy plus REJECT > REPAIR > ACCEPT precedence. |
| REQ | PIPE-04 | Per-record ledger with issue/action/reason/original/normalized values | 01-02 | COVERED | Typed nested issue and normalization evidence. |
| REQ | PIPE-05 | Row conservation and deterministic reruns | 01-01, 01-02, 01-04 | COVERED | Tracer, full-output, and clean-root rerun tests. |
| REQ | PIPE-06 | Queryable typed Parquet with schema/rationale | 01-01, 01-02, 01-04 | COVERED | DuckDB writer, schema JSON, report/README rationale. |
| REQ | PIPE-07 | Highest-ERROR service from executable analysis | 01-03, 01-04 | COVERED | SQL 01, CSV 01, report evidence chain. |
| REQ | PIPE-08 | UTC daily error counts and honest unusual-day rule | 01-03, 01-04 | COVERED | SQL 02, CSV 02, strict D-11 rule/ratio and D-13 wording. |
| REQ | PIPE-09 | Top three normalized errors and services | 01-03, 01-04 | COVERED | SQL 03 ranks primary signatures; CSV/report show service detail. |
| REQ | PIPE-10 | Repaired/rejected counts grouped by issue and reconciled | 01-03, 01-04 | COVERED | SQL 04 separates issue occurrences and final-action records. |
| REQ | PIPE-11 | Every answer links dataset, analysis source, result, manifest | 01-01, 01-03, 01-04 | COVERED | Manifest analysis entries and report-side evidence chains. |
| RESEARCH | — | Python `>=3.12,<3.15`, uv lock, DuckDB 1.5.5, pytest 9.1.1, Ruff 0.16.2 | 01-01 | COVERED | Package legitimacy gate precedes bootstrap/install. |
| RESEARCH | — | Envelope every physical line before JSON parsing | 01-01, 01-02 | COVERED | Tracer proves seam; full reader accounts all lines. |
| RESEARCH | — | Collect all issues then derive one final action | 01-02 | COVERED | Typed issue list and tested precedence. |
| RESEARCH | — | Stable atomic artifacts and deterministic reruns | 01-01, 01-02, 01-03, 01-04 | COVERED | Atomic writers, fixed order/config, repeated-output tests. |
| RESEARCH | — | JSONL ledger plus DuckDB Parquet and fixed schema | 01-01, 01-02 | COVERED | Phase-wide data contracts and committed base evidence. |
| RESEARCH | — | Static SQL, parameterized paths, dedicated DuckDB connection | 01-01, 01-03 | COVERED | Tracer SQL plus four production queries. |
| RESEARCH | — | Four deterministic result tables | 01-03 | COVERED | One CSV per customer question. |
| RESEARCH | — | Report and manifest render evidence rather than recalculate | 01-04 | COVERED | Evidence-only renderer and tamper tests. |
| RESEARCH | — | Maximum-line, output-path, and source-overwrite controls | 01-01, 01-02, 01-04 | COVERED | 1 MiB pre-parse limit, resolved-root guard, exact clean targets. |
| RESEARCH | — | A1: prove byte-identical Parquet on locked platform | 01-01, 01-02, 01-04 | COVERED | Tracer and full rerun hash tests catch writer metadata variance early. |
| RESEARCH | — | A2: require explicit timestamp offset | 01-02 | COVERED | Dedicated issue code, documentation, unit tests. |
| RESEARCH | — | Unknown service vs known level policy | 01-02 | COVERED | Known-level allowlist; non-empty unknown service retained and documented. |
| RESEARCH | — | No observed repair should remain explicit zero | 01-02, 01-03 | COVERED | Repair branch exists; quality CSV retains zero REPAIR row. |
| CONTEXT | D-01 | Conservative, provable repair only | 01-02 | COVERED | Task 1 policy/action/test citations. |
| CONTEXT | D-02 | Reject malformed JSON, invalid timestamp, required-field gaps | 01-02 | COVERED | Task 1 behavior/action/acceptance citations. |
| CONTEXT | D-03 | Retain first exact duplicate; reject/cross-reference later copies | 01-02 | COVERED | Task 1 duplicate digest and ledger contract. |
| CONTEXT | D-04 | UTC representation change is normalization, not repair | 01-01, 01-02 | COVERED | Raw/normalized fields and separate normalization evidence. |
| CONTEXT | D-05 | Retain all issues; REJECT > REPAIR > ACCEPT | 01-02, 01-03 | COVERED | Typed issue list, precedence test, separate count units. |
| CONTEXT | D-06 | Stable semantic ERROR signatures including HTTP_502 | 01-01, 01-02, 01-03 | COVERED | Tracer, complete parser, top-three SQL. |
| CONTEXT | D-07 | Secondary embedded dimensions do not fragment ranking | 01-01, 01-02, 01-03 | COVERED | Clean schema and primary-group SQL. |
| CONTEXT | D-08 | Preserve raw; retain/report UNCLASSIFIED_ERROR | 01-02, 01-03, 01-04 | COVERED | Fallback, count table, report warning. |
| CONTEXT | D-09 | ERROR-only taxonomy | 01-01, 01-02, 01-03 | COVERED | Null INFO/WARN taxonomy and SQL filter. |
| CONTEXT | D-10 | UTC official dates, preserved raw/offset, seven-day window | 01-01, 01-02, 01-03 | COVERED | Normalizer plus daily SQL. |
| CONTEXT | D-11 | Strict >2x median descriptive heuristic and ratio | 01-03, 01-04 | COVERED | SQL calculation and report wording. |
| CONTEXT | D-12 | Accepted/repaired daily counts; rejects separate | 01-02, 01-03 | COVERED | Parquet gate and ledger quality SQL. |
| CONTEXT | D-13 | Flagged-day service contributions without causal claims | 01-03, 01-04 | COVERED | Daily SQL and report behavior tests. |
| CONTEXT | D-14 | Canonical end-to-end plus independent stage commands | 01-01, 01-04 | COVERED | Durable CLI skeleton, Make targets, README. |
| CONTEXT | D-15 | One Markdown primary report with all answers/method/quality | 01-04 | COVERED | Evidence-only renderer and committed report. |
| CONTEXT | D-16 | Direct SQL/result/hash/count/manifest evidence chain per answer | 01-01, 01-04 | COVERED | Tracer seam, manifest entries, report links. |
| CONTEXT | D-17 | Commit and regeneratively verify full deterministic snapshot | 01-02, 01-03, 01-04 | COVERED | Base artifacts, tables, report/manifest, canonical gate. |

## Spec-less Edge Coverage Accounting

Every raw deterministic probe row is represented below and maps to a `must_haves.truths` or `must_haves.flagged_assumptions` entry in the cited plan.

| Requirement | Category | Disposition | Plan | Authored predicate / flagged assumption |
|---|---|---|---|---|
| RPRO-01 | idempotency | resolved / explicit | 01-01 | Repeated locked tracer/full runs have stable artifacts and unchanged source hashes. |
| RPRO-01 | concurrency | unresolved / flagged | 01-01 | No coordinated same-output-root parallel-writer contract is source-defined. |
| RPRO-02 | unclassified | unresolved / flagged | 01-01 | Complete `docs/onboard` hash-scope assumption is surfaced. |
| PIPE-01 | adjacency | resolved / explicit | 01-02 | Exact duplicates stay distinct ledger lines; later rows point to the first. |
| PIPE-01 | empty | unresolved / flagged | 01-02 | Whole-empty-input behavior is not source-defined. |
| PIPE-01 | ordering | resolved / explicit | 01-02 | Ledger and analytical records preserve stable source-line order. |
| PIPE-02 | adjacency | unresolved / flagged | 01-02 | Same-code repetition inside one record lacks source-defined collapse semantics. |
| PIPE-02 | empty | unresolved / flagged | 01-02 | Null/missing records reject, but empty-dataset validation outcome is unspecified. |
| PIPE-02 | ordering | resolved / explicit | 01-02 | Issues emit in deterministic catalogue order. |
| PIPE-03 | adjacency | resolved / explicit | 01-02 | Duplicate and multi-issue records follow explicit D-03/D-05 rules. |
| PIPE-03 | empty | resolved / explicit | 01-02 | Issue-free parseable records ACCEPT; null/missing required content REJECTS. |
| PIPE-03 | ordering | resolved / explicit | 01-02 | REJECT precedes REPAIR, which precedes ACCEPT. |
| PIPE-03 | concurrency | unresolved / flagged | 01-02 | Pure validation is deterministic; concurrent output coordination is unspecified. |
| PIPE-04 | unclassified | unresolved / flagged | 01-02 | One ledger record per physical line with nested issues/normalizations is surfaced as the assumed auditable shape. |
| PIPE-05 | adjacency | resolved / explicit | 01-02 | Duplicate rows reconcile separately rather than merge silently. |
| PIPE-05 | empty | unresolved / flagged | 01-02 | Empty-source Parquet behavior is not source-defined. |
| PIPE-05 | ordering | resolved / explicit | 01-02 | Stable source/row/artifact order is tested across reruns. |
| PIPE-06 | unclassified | unresolved / flagged | 01-02 | Fixed schema/rationale visibility is surfaced as the structured-dataset interpretation. |
| PIPE-07 | unclassified | unresolved / flagged | 01-03 | Stable first-ranked service interpretation is surfaced. |
| PIPE-08 | unclassified | unresolved / flagged | 01-03 | D-11/D-13 are explicitly retained as authoritative. |
| PIPE-09 | unclassified | unresolved / flagged | 01-03 | Primary semantic error grouping with secondary services is surfaced. |
| PIPE-10 | unclassified | unresolved / flagged | 01-03 | Issue-occurrence and record-action counting units are both surfaced. |
| PIPE-11 | adjacency | resolved / explicit | 01-03 | Equal counts remain separate; stable alphabetical tie-breakers define the boundary. |
| PIPE-11 | empty | unresolved / flagged | 01-03 | Empty-cleaned-dataset answer wording is not source-defined. |
| PIPE-11 | ordering | resolved / explicit | 01-03 | Every result table has explicit deterministic ordering. |

**Equality check:** 25 probe rows = 11 resolved truths + 14 flagged assumptions. No row was dismissed.

## Prohibition Recall Accounting

Kept, descriptor-less, flagged/unverified bespoke prohibitions:

1. Plan 01-02 — the pipeline must not alter source bytes, invent missing values, or mislabel normalization as repair.
2. Plan 01-03 — daily findings must not become statistical-anomaly or causal-service claims.
3. Plan 01-04 — reported answers must not become manually transcribed numbers without the complete evidence chain.

Canon breadcrumbs dropped rather than minted: unsafe path handling and SQL injection are covered by the Phase 1 threat models and `$gsd-secure-phase`; package supply-chain risk is covered by the blocking legitimacy gate; generic secret/privacy checks belong to the security/final submission audits.

## Capability Detector Results

- API coverage detector: `detected=false`; no external API/SDK/service is integrated, so no `COVERAGE.md` declaration or capability matrix is required.
- Assumption-delta scan: `detected=false`; no identity-model decision is injected.
- Schema-push scan: no Payload, Prisma, Drizzle, Supabase, or TypeORM signal; no ORM push task is fabricated.
- Knowledge graph: absent; planning used current source artifacts directly.
- Discovery: existing same-day Phase 1 research satisfies Level 2 external-dependency research; package installation remains behind the required legitimacy checkpoint.
