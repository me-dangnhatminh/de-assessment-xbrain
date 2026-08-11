# Requirements: Xbrain Data Engineer Assessment POC

**Defined:** 2026-08-11
**Core Value:** Every claimed result must be reproducible, source-grounded, and understandable enough for the candidate to defend in a technical interview.

## v1 Requirements

Requirements for the complete assessment submission. Each requirement will map to exactly one roadmap phase.

### Reproducibility Foundation

- [ ] **RPRO-01**: Reviewer can create the documented, locked Python environment and invoke the project verification commands from a clean checkout.
- [ ] **RPRO-02**: Reviewer can verify that supplied briefs, readings, logs, and operational documents remain unchanged through recorded source hashes.
- [ ] **RPRO-03**: Reviewer can inspect an evidence manifest that records input hashes, relevant configuration, commands, output paths, row counts, and non-secret runtime metadata for generated results.
- [ ] **RPRO-04**: Reviewer can run a clean-output smoke check that regenerates required deterministic artifacts and verifies their internal consistency.
- [ ] **RPRO-05**: Reviewer can configure AWS and Bedrock access without any credential, account identifier, or real `.env` file being committed.

### Log Pipeline and Analysis

- [x] **PIPE-01**: Reviewer can run a Python command that reads every line of `docs/onboard/datapack/data/app_logs_7days.jsonl` while retaining source-line provenance.
- [x] **PIPE-02**: Reviewer can inspect validation code that detects and assigns stable issue codes to every discovered JSON, schema, type, timestamp, categorical, and content-quality problem.
- [x] **PIPE-03**: Reviewer can inspect an explicit rule and rationale for whether each issue type is accepted, narrowly repaired, or rejected without editing the source file.
- [x] **PIPE-04**: Reviewer can inspect a per-record quality ledger containing source line, issue code, action, reason, and original versus normalized values where a repair occurs.
- [ ] **PIPE-05**: Reviewer can verify row conservation and deterministic reruns: every input record is accounted for and repeated runs with the same inputs produce the same cleaned data and quality totals.
- [ ] **PIPE-06**: Reviewer can query a structured Parquet dataset with a documented schema and a concise rationale for choosing the format.
- [ ] **PIPE-07**: Reviewer can reproduce which service has the most `ERROR` records across the seven-day period from checked-in SQL or pandas code and recorded results.
- [ ] **PIPE-08**: Reviewer can reproduce system-wide daily error counts and inspect the stated, evidence-based rule used to identify any unusual day without overstating statistical certainty.
- [ ] **PIPE-09**: Reviewer can reproduce the three most frequent normalized error types or codes and the associated service or services.
- [ ] **PIPE-10**: Reviewer can reproduce rejected and repaired record counts grouped by issue type, with totals reconciling to the quality ledger.
- [ ] **PIPE-11**: Reviewer can trace every reported pipeline answer to the cleaned dataset, executable analysis source, generated result table, and run manifest rather than to manual calculations.

### AWS Daily-Pipeline Design

- [ ] **AWS-01**: Reviewer can view a legible architecture diagram showing the proposed daily AWS data flow from ingestion and raw storage through validation, quarantine, curated storage, cataloging, and query/report access.
- [ ] **AWS-02**: Reviewer can read an English explanation of no more than one page that justifies the selected AWS services and distinguishes the conceptual design from the locally implemented POC.
- [ ] **AWS-03**: Reviewer can identify least-privilege IAM boundaries, monitoring or failure handling, and explicitly unresolved assumptions or uncertainties in the AWS design.

### Version-Aware Knowledge Base

- [ ] **KB-01**: Reviewer can verify from an inventory that all eight supplied operational documents are processed and attributable to their source files.
- [ ] **KB-02**: Reviewer can inspect structure-based chunking rules that preserve headings, tables, and procedure steps, with documented handling for exceptional sections.
- [ ] **KB-03**: Reviewer can inspect each chunk's source document, section, version, issue or effective date, owner, active or superseded status, and content hash, with unavailable metadata represented as missing rather than invented.
- [ ] **KB-04**: Reviewer can rebuild and query a lightweight SQLite FTS5 index from the document inventory and chunk records using documented commands.
- [ ] **KB-05**: Reviewer receives current-policy results by applying effective-version status before relevance ranking, while superseded content remains explicitly available for historical inspection.
- [ ] **KB-06**: Reviewer can trace every retrieval result and generated answer used in evaluation to versioned source documents and section or chunk identifiers.
- [ ] **KB-07**: Reviewer can inspect ten predeclared evaluation questions with expected answers, expected source sections, and explicit pass, partial-pass, and fail criteria.
- [ ] **KB-08**: Reviewer can verify the evaluation set includes direct lookup, multi-source synthesis, the intentional version conflict, and an out-of-scope refusal case.
- [ ] **KB-09**: Reviewer can inspect recorded executions for at least three evaluation questions, including the query, retrieved evidence, answer, score, and diagnosis.
- [ ] **KB-10**: Reviewer can distinguish retrieval hit or miss from answer groundedness in each executed evaluation rather than receiving a single opaque score.
- [ ] **KB-11**: Reviewer can inspect saved ranked retrieval traces and an explicit demonstration that `POL-01` v2 wins current-policy queries while v1 remains identifiable as superseded history.
- [ ] **KB-12**: Reviewer receives a clear “not found in the supplied documents” outcome for unsupported questions instead of an invented operational answer.

### Knowledge-Base Update SOP

- [ ] **SOP-01**: Reviewer can read an English knowledge-base update SOP of no more than one page covering new documents, revised documents, metadata and version validation, re-indexing, regression evaluation, approval, and rollback or history retention.
- [ ] **SOP-02**: Reviewer can identify the update cadence and the accountable owner, technical operator, and approver for each SOP control without relying on unstated assumptions.

### AI Work Log

- [ ] **AILOG-01**: Reviewer can inspect 8–15 genuine, chronologically plausible `AI_WORKLOG.md` entries for material AI-assisted coding, design, documentation, debugging, or evaluation work.
- [ ] **AILOG-02**: Each work-log entry records the task, meaningful prompt or prompt summary, AI output and critical assessment, and the independent verification and corrections performed before use.
- [ ] **AILOG-03**: Reviewer can identify honest limitations and at least one genuine correction of an AI mistake if such a mistake occurs, while every retained artifact remains explainable by the candidate.

### AI Response Review

- [ ] **AIREV-01**: Reviewer can read an English review of no more than one page that addresses every incorrect, misleading, absolute, or context-dependent claim in the supplied AWS and RAG response.
- [ ] **AIREV-02**: For each reviewed claim, reviewer can see what is wrong, why it is wrong, and a technically accurate replacement or conditional recommendation.
- [ ] **AIREV-03**: Reviewer can audit a compact claim-to-source mapping that grounds corrections in current official AWS documentation, the supplied readings, or explicitly identified practical evidence.

### Structured Extraction Prompt and Bedrock Trial

- [ ] **AIEXT-01**: Reviewer can inspect an English, two-page-or-shorter extraction task containing a complete prompt with role, input contract, processing rules, and output contract.
- [ ] **AIEXT-02**: Reviewer can validate model output against a strict JSON schema for error type, related component, extracted parameters, and explicit uncertainty or parse status.
- [ ] **AIEXT-03**: Reviewer can verify the prompt requires missing or ambiguous values to be represented explicitly and forbids unsupported inference or fabricated fields.
- [ ] **AIEXT-04**: Reviewer can inspect five test messages selected from the supplied data, including at least one difficult or ambiguous case, with expected JSON for each.
- [ ] **AIEXT-05**: Reviewer can inspect a measurable 3,000-line evaluation plan covering schema validity, field-level correctness, unsupported-value or hallucination rate, parse coverage, sampling, and human-review thresholds.
- [ ] **AIEXT-06**: Reviewer can run a Bedrock preflight that verifies configured credentials, Region, permitted model or inference profile, and compatible inference API without exposing secrets.
- [ ] **AIEXT-07**: Reviewer can execute all five fixed cases through Amazon Bedrock using configurable model and Region settings and bounded, recorded inference parameters.
- [ ] **AIEXT-08**: Reviewer can inspect each raw Bedrock response, locally validated JSON result, expected-versus-actual field comparison, and pass or fail diagnosis without silent repair.
- [ ] **AIEXT-09**: Reviewer can inspect non-secret Bedrock trial metadata and honest observations about model variability, unsupported features, failures, and prompt improvements.
- [ ] **AIEXT-10**: Reviewer can rerun the deterministic comparison and reporting step without repeating paid model calls when saved raw Bedrock responses are available.

### Submission and Handoff

- [ ] **DOC-01**: Reviewer can navigate the required top-level deliverables: `pipeline/`, `kb/`, `design/`, `sop/`, `AI_WORKLOG.md`, and the root `README.md`.
- [ ] **DOC-02**: Reviewer can use the English root README to understand the project, set it up, run each part, locate outputs, and review decisions, rationale, assumptions, limitations, uncertainties, and anything unfinished.
- [ ] **DOC-03**: Reviewer encounters English throughout all submitted documentation, reports, code comments, evaluation fixtures, and generated reviewer-facing outputs.
- [ ] **DOC-04**: Reviewer can inspect a limitations register that separates verified results, design assumptions, account-dependent behavior, and deliberately deferred work.
- [ ] **DOC-05**: Reviewer can verify required files, page limits, tests, lint, secrets hygiene, reproducibility commands, and source integrity through a final submission audit.
- [ ] **DOC-06**: Reviewer can inspect genuine incremental Git history and receive a repository ready for GitHub sharing and ZIP backup without generated secrets or accidental local state.

## v2 Requirements

No v2 capabilities are planned for this fixed-scope assessment. Any expansion requires an explicit scope decision after the submission is complete.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Live deployment of the AWS data pipeline | The brief asks for an on-paper design; deployment adds cost and operational risk without satisfying another requirement. |
| Terraform, CDK, or other infrastructure provisioning | No infrastructure deployment is required within the two-day assessment. |
| Dashboard, web UI, or conversational assistant interface | Reviewable CLI outputs and evidence satisfy the POC; presentation layers would consume time without improving the assessed capabilities. |
| Vector database, embeddings, or RAG framework | SQLite FTS5 is sufficient and more explainable for eight structured documents unless empirical evaluation proves otherwise. |
| Streaming or distributed log processing | The supplied seven-day dataset and requested daily AWS design do not justify that complexity. |
| LLM-based log cleaning or live inference over all 3,000 lines | Deterministic cleaning is required; Task B asks for five live cases and an evaluation method for 3,000 lines, not a full production batch. |
| Modification of supplied inputs | Raw logs, documents, briefs, and readings must remain immutable for auditability and reproducibility. |
| Invented operational facts or metadata | Unsupported content would fail groundedness and undermine the assessment's verification goals. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| RPRO-01 | Phase 1 | Pending |
| RPRO-02 | Phase 1 | Pending |
| RPRO-03 | Phase 4 | Pending |
| RPRO-04 | Phase 4 | Pending |
| RPRO-05 | Phase 3 | Pending |
| PIPE-01 | Phase 1 | Complete |
| PIPE-02 | Phase 1 | Complete |
| PIPE-03 | Phase 1 | Complete |
| PIPE-04 | Phase 1 | Complete |
| PIPE-05 | Phase 1 | Pending |
| PIPE-06 | Phase 1 | Pending |
| PIPE-07 | Phase 1 | Pending |
| PIPE-08 | Phase 1 | Pending |
| PIPE-09 | Phase 1 | Pending |
| PIPE-10 | Phase 1 | Pending |
| PIPE-11 | Phase 1 | Pending |
| AWS-01 | Phase 3 | Pending |
| AWS-02 | Phase 3 | Pending |
| AWS-03 | Phase 3 | Pending |
| KB-01 | Phase 2 | Pending |
| KB-02 | Phase 2 | Pending |
| KB-03 | Phase 2 | Pending |
| KB-04 | Phase 2 | Pending |
| KB-05 | Phase 2 | Pending |
| KB-06 | Phase 2 | Pending |
| KB-07 | Phase 2 | Pending |
| KB-08 | Phase 2 | Pending |
| KB-09 | Phase 2 | Pending |
| KB-10 | Phase 2 | Pending |
| KB-11 | Phase 2 | Pending |
| KB-12 | Phase 2 | Pending |
| SOP-01 | Phase 2 | Pending |
| SOP-02 | Phase 2 | Pending |
| AILOG-01 | Phase 4 | Pending |
| AILOG-02 | Phase 4 | Pending |
| AILOG-03 | Phase 4 | Pending |
| AIREV-01 | Phase 3 | Pending |
| AIREV-02 | Phase 3 | Pending |
| AIREV-03 | Phase 3 | Pending |
| AIEXT-01 | Phase 3 | Pending |
| AIEXT-02 | Phase 3 | Pending |
| AIEXT-03 | Phase 3 | Pending |
| AIEXT-04 | Phase 3 | Pending |
| AIEXT-05 | Phase 3 | Pending |
| AIEXT-06 | Phase 3 | Pending |
| AIEXT-07 | Phase 3 | Pending |
| AIEXT-08 | Phase 3 | Pending |
| AIEXT-09 | Phase 3 | Pending |
| AIEXT-10 | Phase 3 | Pending |
| DOC-01 | Phase 4 | Pending |
| DOC-02 | Phase 4 | Pending |
| DOC-03 | Phase 4 | Pending |
| DOC-04 | Phase 4 | Pending |
| DOC-05 | Phase 4 | Pending |
| DOC-06 | Phase 4 | Pending |

**Coverage:**

- v1 requirements: 55 total
- Mapped to phases: 55
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-11*
*Last updated: 2026-08-11 after roadmap creation*
