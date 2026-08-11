# Phase 1: Auditable Log Pipeline & Analysis - Context

**Gathered:** 2026-08-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a local, reviewer-runnable Python workflow that proves source integrity, accounts for every input log line through explicit quality decisions, produces a typed cleaned Parquet dataset, and reproduces the four requested customer analyses with committed evidence. AWS deployment design, knowledge-base work, Bedrock trials, and final repository handoff remain in later phases.

</domain>

<decisions>
## Implementation Decisions

### Dirty-record disposition
- **D-01:** Use conservative repair. Repair only defects whose intended value is lossless, unambiguous, and mechanically provable; never infer missing values from message meaning.
- **D-02:** Reject malformed JSON, invalid timestamps, and records missing fields required for the analysis rather than inventing replacements.
- **D-03:** For exact duplicate records, retain the first occurrence in cleaned Parquet and reject later copies. The quality ledger must cross-reference the retained and rejected source lines.
- **D-04:** Treat valid representation changes, such as converting an offset timestamp to the same UTC instant, as normalization rather than repair. Preserve original and normalized representations in evidence without inflating repaired-record totals.
- **D-05:** Capture every detected issue separately. Retain a record-level final action determined by explicit precedence: reject overrides repair, and repair overrides accept.

### Error normalization
- **D-06:** Normalize `ERROR` messages to stable semantic signatures parsed from the explicit error token, with structured handling where required, such as `HTTP_502`.
- **D-07:** Keep embedded values such as error codes, related components, and paths as secondary structured dimensions. They must not fragment the primary error-type ranking.
- **D-08:** Preserve every raw message. If a valid `ERROR` record does not match a known signature, retain it with `error_type = UNCLASSIFIED_ERROR` and report the unclassified count as a normalization-quality warning.
- **D-09:** Apply the error taxonomy only to `level=ERROR`. INFO and WARN messages remain available as raw content but do not require a general event taxonomy in this phase.

### Day boundaries and unusual-day language
- **D-10:** Normalize valid timestamp instants to UTC and use the UTC calendar date for the official daily report. Preserve the original timestamp and offset for provenance. This produces the advertised seven-day window from 2026-07-27 through 2026-08-02.
- **D-11:** Flag a day as unusual only when its cleaned error count exceeds twice the median daily error count. Report the observed ratio and describe the rule as a descriptive seven-day heuristic, not a statistical anomaly detector.
- **D-12:** Calculate daily counts only from accepted or repaired analytical records. Disclose rejected records and their reasons separately in the quality reconciliation instead of assigning them an artificial date.
- **D-13:** For each flagged day, show error contributions by service while avoiding unsupported claims about causation.

### Reviewer evidence experience
- **D-14:** Provide one canonical end-to-end command covering source-integrity checks, ingestion, cleaning, analysis, and verification. Also expose each stage through independently runnable commands.
- **D-15:** Generate one Markdown report as the primary review surface, containing all four customer answers, concise methodology notes, quality totals, unusual-day reasoning, and paths to detailed evidence.
- **D-16:** Place a direct evidence chain beside every reported answer: the SQL query, generated result table, cleaned-dataset hash, relevant row counts, and run-manifest entry.
- **D-17:** Commit the complete deterministic Phase 1 evidence snapshot: cleaned Parquet, full quality ledger, analysis tables, Markdown report, and manifest. Verification must regenerate the artifacts and check their hashes or internal consistency.

### the agent's Discretion
- Exact stable issue-code names, schema column names, module boundaries, CLI flag names, and output directory layout are left to research and planning, provided they preserve the decisions and evidence contracts above.
- The exact parser implementation for each recognized error signature is flexible, but rules must be explicit, deterministic, tested, and preserve raw messages.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project scope and acceptance requirements
- `.planning/PROJECT.md` — Defines the core value, fixed two-day scope, immutable-input rule, required submission shape, and project-level decisions.
- `.planning/REQUIREMENTS.md` — Defines Phase 1 requirements RPRO-01, RPRO-02, and PIPE-01 through PIPE-11, including traceability and evidence expectations.
- `.planning/ROADMAP.md` — Defines the Phase 1 goal, boundaries, dependencies, and success criteria.
- `.planning/research/STACK.md` — Records the researched local-first stack recommendations and reproducibility boundaries relevant to Phase 1 planning.

### Assessment and supplied data
- `docs/onboard/01_Domain_POC.md` — Authoritative assessment brief for the local pipeline and four customer questions.
- `docs/onboard/datapack/README.md` — Defines the supplied seven-day data pack and the explicit instruction not to edit source data.
- `docs/onboard/datapack/data/app_logs_7days.jsonl` — Immutable canonical input whose lines, anomalies, and hashes drive Phase 1 behavior and evidence.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No pipeline implementation exists yet. The repository currently provides the immutable source log, assessment brief, planning requirements, and stack research as the reusable foundation.

### Established Patterns
- There are no established application-code conventions yet. New code must therefore make validation, disposition, and evidence flow explicit rather than relying on an existing abstraction.
- Planning already favors a local-first, reproducible, explainable implementation and requires generated artifacts to live outside the supplied input tree.

### Integration Points
- New implementation belongs under the required top-level `pipeline/` area.
- The eventual root `README.md` must expose the canonical end-to-end command and stage commands; it is currently empty.
- Phase 1 outputs must be suitable for later final-manifest and submission-audit work without requiring source mutation or manual recalculation.

</code_context>

<specifics>
## Specific Ideas

- The source scan found malformed JSON, missing levels, invalid timestamps, optional `trace_id` fields, mixed `Z` and `+07:00` offsets, and exact duplicate records. Planning must cover these observed classes without assuming they are the exhaustive validation taxonomy.
- Stable error signatures discussed include `SMTPConnRefused`, `PaymentDeclined`, `ConnTimeout`, `NullPointer`, and `HTTP_502`.
- The primary report should optimize for an evaluator who wants immediate conclusions but can follow every result into machine-readable evidence.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Auditable Log Pipeline & Analysis*
*Context gathered: 2026-08-11*
