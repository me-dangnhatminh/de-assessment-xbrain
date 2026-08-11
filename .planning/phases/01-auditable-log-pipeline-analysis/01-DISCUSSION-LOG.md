# Phase 1: Auditable Log Pipeline & Analysis - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-11
**Phase:** 1-Auditable Log Pipeline & Analysis
**Areas discussed:** Dirty-record disposition, Error normalization, Day boundaries and unusual-day language, Reviewer evidence experience

---

## Dirty-record disposition

### Repair threshold

| Option | Description | Selected |
|--------|-------------|----------|
| Conservative repair | Repair only lossless, mechanically provable defects; reject malformed JSON, invalid timestamps, and missing analysis-critical fields; never infer values from message meaning. | ✓ |
| Strict rejection | Reject every canonical-schema violation and perform only representation normalization after acceptance. | |
| Maximum deterministic salvage | Recover malformed or missing values whenever a documented rule can derive a plausible result. | |

**User's choice:** Conservative repair
**Notes:** No free-text qualification was added.

### Exact duplicates

| Option | Description | Selected |
|--------|-------------|----------|
| Exclude later copies | Keep the first occurrence, reject later exact duplicates from cleaned Parquet, and cross-reference source lines in the ledger. | ✓ |
| Retain and flag | Keep every duplicate with an `is_duplicate` marker and make analyses choose whether to include them. | |
| Retain as valid | Treat identical events as potentially legitimate unless additional evidence proves duplication. | |

**User's choice:** Exclude later copies
**Notes:** Duplicate exclusion must remain row-conserving through the quality ledger.

### Representation normalization

| Option | Description | Selected |
|--------|-------------|----------|
| Separate normalization from repair | Accept valid records, retain original and normalized representations, and reserve repaired counts for actual quality corrections. | ✓ |
| Every changed value is a repair | Count any source-to-output value transformation as a repair. | |
| Preserve valid representations unchanged | Avoid representation changes even when the cleaned dataset would retain mixed timestamp formats. | |

**User's choice:** Separate normalization from repair
**Notes:** Converting a valid offset timestamp to the same UTC instant is normalization, not repair.

### Multiple issues on one record

| Option | Description | Selected |
|--------|-------------|----------|
| Capture every issue | Emit one ledger entry per issue and use reject-over-repair-over-accept precedence for the record action. | ✓ |
| Stop at the first issue | Record only the first validation failure encountered. | |
| Use one composite result | Store all issue codes together in one record-level entry. | |

**User's choice:** Capture every issue
**Notes:** Every discovered issue remains auditable even when another issue determines rejection.

---

## Error normalization

### Primary error type

| Option | Description | Selected |
|--------|-------------|----------|
| Stable semantic signature | Parse the explicit error token, with structured handling such as `HTTP_502`; preserve raw messages and parameters. | ✓ |
| Parameter-stripped message template | Normalize the complete message shape, potentially splitting similar operational errors. | |
| Exact full message | Count each raw message as its own error type. | |

**User's choice:** Stable semantic signature
**Notes:** Discussed examples include `SMTPConnRefused`, `PaymentDeclined`, `ConnTimeout`, `NullPointer`, and `HTTP_502`.

### Embedded codes and components

| Option | Description | Selected |
|--------|-------------|----------|
| Primary type plus secondary dimensions | Keep error code, related component, path, and similar values as drill-down fields without fragmenting the primary type. | ✓ |
| Include every code in the primary type | Produce signatures such as `PaymentDeclined_51`. | |
| Discard extracted parameters | Keep only normalized type and raw message. | |

**User's choice:** Primary type plus secondary dimensions
**Notes:** Primary rankings remain stable while detailed evidence remains queryable.

### Unrecognized ERROR messages

| Option | Description | Selected |
|--------|-------------|----------|
| Keep as unclassified | Retain the record with `UNCLASSIFIED_ERROR`, preserve the raw message, and report a warning count. | ✓ |
| Generate a fallback type | Derive a deterministic parameter-stripped phrase from the message. | |
| Reject the record | Exclude messages that do not match the known taxonomy. | |

**User's choice:** Keep as unclassified
**Notes:** Classification coverage is separate from record validity.

### Taxonomy scope

| Option | Description | Selected |
|--------|-------------|----------|
| ERROR only | Populate normalized error fields only for `level=ERROR`; preserve INFO and WARN messages without a general taxonomy. | ✓ |
| ERROR and WARN | Normalize errors and warning families. | |
| All levels | Classify every log message into an event type. | |

**User's choice:** ERROR only
**Notes:** This keeps Phase 1 bounded to the requested analysis.

---

## Day boundaries and unusual-day language

### Official calendar

| Option | Description | Selected |
|--------|-------------|----------|
| UTC day | Normalize valid instants to UTC, group by UTC date, and preserve original timestamps and offsets. | ✓ |
| Vietnam operational day | Convert all instants to `Asia/Ho_Chi_Minh` before deriving the report date. | |
| Publish both calendars | Provide primary and supporting daily tables. | |

**User's choice:** UTC day
**Notes:** The source scan showed that UTC grouping produces exactly the advertised 2026-07-27 through 2026-08-02 window; Vietnam-time grouping produces parts of eight dates.

### Unusual-day rule

| Option | Description | Selected |
|--------|-------------|----------|
| Twice-the-median heuristic | Flag only a day above twice the median, show the ratio, and describe the result as a seven-day descriptive heuristic. | ✓ |
| Median plus three MADs | Use a robust median-absolute-deviation threshold. | |
| Maximum only | Identify the highest-count day without calling it unusual. | |

**User's choice:** Twice-the-median heuristic
**Notes:** The wording must not imply a production statistical anomaly detector.

### Rejected records in daily results

| Option | Description | Selected |
|--------|-------------|----------|
| Clean counts plus an exclusion note | Count only accepted or repaired records and reconcile rejected records separately. | ✓ |
| Add an `UNKNOWN_DATE` row | Mix rejected records with unusable timestamps into the daily table when possible. | |
| Attempt a parallel raw-data estimate | Publish a best-effort count derived from rejected source lines. | |

**User's choice:** Clean counts plus an exclusion note
**Notes:** The daily table remains a query over the canonical cleaned dataset.

### Explanation depth

| Option | Description | Selected |
|--------|-------------|----------|
| Add a service contribution breakdown | For flagged days, show errors by service without asserting causation. | ✓ |
| Report only the threshold result | Show totals, median, ratio, and date without service-level detail. | |
| Break down every day by service | Publish the complete date-by-service matrix. | |

**User's choice:** Add a service contribution breakdown
**Notes:** Contribution is evidence; causal explanation would require additional data.

---

## Reviewer evidence experience

### Command path

| Option | Description | Selected |
|--------|-------------|----------|
| One happy-path command plus visible stages | Run integrity, ingestion, cleaning, analysis, and verification end to end while retaining public stage commands. | ✓ |
| Stage commands only | Require the evaluator to run each stage manually in order. | |
| Single opaque runner | Offer only one command with no public stage interface. | |

**User's choice:** One happy-path command plus visible stages
**Notes:** Exact command names remain a planning decision.

### Human-readable result

| Option | Description | Selected |
|--------|-------------|----------|
| Generated Markdown report | Present all four answers, methodology, quality totals, unusual-day reasoning, and detailed evidence paths in one report. | ✓ |
| CSV tables with README narrative | Split results across tables and explain conclusions manually in the README. | |
| Console output only | Treat captured terminal output as the primary evidence. | |

**User's choice:** Generated Markdown report
**Notes:** Machine-readable artifacts remain available beneath the report.

### Per-answer provenance

| Option | Description | Selected |
|--------|-------------|----------|
| Per-answer evidence chain | Identify the SQL query, result table, cleaned-dataset hash, row counts, and manifest entry beside each conclusion. | ✓ |
| One shared provenance appendix | Collect provenance centrally without mapping it to individual answers. | |
| Artifact paths only | Let the evaluator reconstruct relationships among outputs. | |

**User's choice:** Per-answer evidence chain
**Notes:** The report must make traceability immediate rather than implicit.

### Committed outputs

| Option | Description | Selected |
|--------|-------------|----------|
| Complete deterministic evidence snapshot | Commit Parquet, full ledger, analysis tables, Markdown report, and manifest; regenerate and verify them. | ✓ |
| Compact evidence only | Commit reports, result tables, summaries, and manifest while regenerating Parquet and the full ledger. | |
| No generated outputs | Commit only implementation source and require a complete local build. | |

**User's choice:** Complete deterministic evidence snapshot
**Notes:** Verification must compare hashes or internal consistency, not merely rerun commands.

---

## the agent's Discretion

- Exact issue-code names and schema column names.
- Module boundaries, CLI flag names, and output directory layout.
- Exact deterministic parser implementation for each recognized error signature.

## Deferred Ideas

None — discussion stayed within Phase 1 scope.
