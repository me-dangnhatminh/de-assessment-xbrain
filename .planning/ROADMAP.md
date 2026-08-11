# Roadmap: Xbrain Data Engineer Assessment POC

## Overview

Deliver a reviewer-defensible assessment submission in four vertical slices: first make the dirty-log findings reproducible, then provide a version-aware operational knowledge base, then capture the bounded AWS and Bedrock AI-proficiency evidence, and finally prove the repository can be reviewed, rerun, and handed off safely. Each slice preserves the supplied inputs and produces inspectable evidence rather than relying on manual claims.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3, 4): Planned milestone work
- Decimal phases (for example, 2.1): Urgent insertions between planned phases

- [x] **Phase 1: Auditable Log Pipeline & Analysis** - Turn immutable JSONL logs into a traceable cleaned dataset and reproducible customer answers. (completed 2026-08-12)
- [ ] **Phase 2: Version-Aware Knowledge Base & Evaluation** - Deliver searchable, attributable operational knowledge with deterministic version handling and evaluation evidence.
- [ ] **Phase 3: AWS Design & Bedrock Extraction Evidence** - Deliver the conceptual AWS design and the bounded, source-grounded AI-proficiency artifacts and live trial.
- [ ] **Phase 4: Reviewer-Ready Submission & Handoff** - Assemble, audit, and document a clean, reproducible assessment submission.

## Phase Details

### Phase 1: Auditable Log Pipeline & Analysis

**Goal**: As a reviewer, I want to run the complete log pipeline and customer analysis, so that I can defend every result from immutable source evidence.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: RPRO-01, RPRO-02, PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06, PIPE-07, PIPE-08, PIPE-09, PIPE-10, PIPE-11
**Success Criteria** (what must be TRUE):

  1. From a clean checkout, a reviewer can create the locked environment, verify hashes for every supplied input, and run ingestion without any source file being changed.
  2. A reviewer can follow every input line through stable validation issue codes and documented accept, repair, or reject decisions in a provenance-preserving quality ledger.
  3. A reviewer can rerun the pipeline and obtain row-conserving, deterministic cleaned Parquet data with a documented schema and a concise format rationale.
  4. A reviewer can rerun checked-in analysis and inspect recorded evidence for the highest-error service, daily error pattern, common normalized errors, and reconciled repaired/rejected counts without relying on manual calculations.

**Plans**: 8/8 plans executed

Plans:

**Wave 1**

- [x] 01-01-PLAN.md — Approve the locked toolchain and prove one immutable source line through the complete local evidence path.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Account for every source line through explicit validation, duplicate handling, and conservative disposition.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Normalize analytical rows and publish the deterministic ledger, schema, source manifest, and cleaned Parquet.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-04-PLAN.md — Establish the static-SQL runner and reproduce highest-service and UTC daily results.

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 01-05-PLAN.md — Complete top-error and quality-reconciliation SQL with the full four-table evidence set.

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 01-06-PLAN.md — Generate the direct evidence report/manifest and canonical clean-checkout verification command.

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 01-07-PLAN.md — Close the stale supplied-inventory verification gap and correct the Phase 1 MVP user-story metadata.

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 01-08-PLAN.md — Bind production evidence to the canonical supplied input and independently verify live Parquet/ledger conservation.

### Phase 2: Version-Aware Knowledge Base & Evaluation

**Goal**: A reviewer can search all supplied operational documents, receive current policy by default, inspect historical provenance, and assess the result quality.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: KB-01, KB-02, KB-03, KB-04, KB-05, KB-06, KB-07, KB-08, KB-09, KB-10, KB-11, KB-12, SOP-01, SOP-02
**Success Criteria** (what must be TRUE):

  1. A reviewer can confirm that all eight documents were inventoried and chunked by their structure, with every chunk attributable to source, section, metadata, status, and content hash—or an explicit missing value.
  2. A reviewer can rebuild and query the SQLite FTS5 index using documented commands, receive effective current-policy content before relevance ranking, and deliberately inspect superseded history when requested.
  3. A reviewer can inspect ten predeclared evaluation cases covering direct lookup, multi-source synthesis, the `POL-01` version trap, and an unsupported question, each with expected sources and pass, partial-pass, and fail criteria.
  4. A reviewer can inspect at least three recorded evaluations with ranked retrieval traces, source and chunk citations, separate retrieval and groundedness diagnoses, and an explicit “not found in the supplied documents” outcome when appropriate.
  5. A reviewer can use a one-page-or-shorter English SOP that assigns update cadence, operator, owner, and approver responsibilities while preserving revision history and regression checks.

**Plans**: 2/2 plans authored

Plans:

**Wave 1**

- [x] 02-01-PLAN.md — Inventory, metadata, chunking, version resolution, FTS5 index build, and current-first search with POL-01 proof.

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 02-02-PLAN.md — Author 10 evaluation cases (4-3-2-1 distribution), execute retrieval-only scoring, and write the KB update SOP.

### Phase 3: AWS Design & Bedrock Extraction Evidence

**Goal**: A reviewer can evaluate a bounded AWS proposal and AI-assisted extraction evidence without credential exposure, unstated assumptions, or unverified claims.
**Mode:** mvp
**Depends on**: Phase 1, Phase 2
**Requirements**: RPRO-05, AWS-01, AWS-02, AWS-03, AIREV-01, AIREV-02, AIREV-03, AIEXT-01, AIEXT-02, AIEXT-03, AIEXT-04, AIEXT-05, AIEXT-06, AIEXT-07, AIEXT-08, AIEXT-09, AIEXT-10
**Success Criteria** (what must be TRUE):

  1. A reviewer can configure AWS and Bedrock through documented non-secret settings, run a preflight for Region, model or inference profile, permission, and API compatibility, and find no committed credential material.
  2. A reviewer can view a legible daily AWS pipeline diagram and a one-page-or-shorter English explanation that distinguishes the conceptual design from the POC, including IAM boundaries, failure handling, and unresolved assumptions.
  3. A reviewer can inspect a one-page-or-shorter English review that corrects each misleading supplied AI claim and links each correction to authoritative AWS documentation, supplied guidance, or identified practical evidence.
  4. A reviewer can inspect a two-page-or-shorter strict JSON extraction prompt, five representative expected-output fixtures (including ambiguity), and a measurable 3,000-line evaluation method that prohibits fabricated values.
  5. A reviewer can run all five fixed Bedrock cases and inspect saved raw responses, local schema validation, field-level expected-versus-actual comparisons, non-secret invocation metadata, honest observations, and a deterministic re-report that does not make new paid calls.

**Plans**: TBD

### Phase 4: Reviewer-Ready Submission & Handoff

**Goal**: A reviewer can independently navigate, verify, and receive the complete submission with honest limits and reproducible evidence.
**Mode:** mvp
**Depends on**: Phase 1, Phase 2, Phase 3
**Requirements**: RPRO-03, RPRO-04, AILOG-01, AILOG-02, AILOG-03, DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06
**Success Criteria** (what must be TRUE):

  1. A reviewer can navigate the required top-level deliverables and use an English root README to set up, run every part, locate outputs, and understand decisions, assumptions, limitations, and unfinished items.
  2. A reviewer can inspect a consolidated evidence manifest that connects input hashes, configuration, commands, output locations, row counts, and non-secret runtime metadata to generated results.
  3. A reviewer can run a clean-output smoke check and final submission audit that regenerate deterministic artifacts and verify required paths, page limits, tests, lint, source integrity, secrets hygiene, and English reviewer-facing material.
  4. A reviewer can inspect 8–15 genuine and chronologically plausible AI-worklog entries containing prompts, critical assessments, independent verification, corrections, and honest limitations.
  5. A reviewer can inspect an explicit limitations register and genuine incremental Git history, then receive a repository ready for GitHub sharing and ZIP backup without secrets or accidental local state.

**Plans**: TBD

## Progress

**Execution Order:** Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Auditable Log Pipeline & Analysis | 8/8 | Complete    | 2026-08-12 |
| 2. Version-Aware Knowledge Base & Evaluation | 1/2 | In Progress | - |
| 3. AWS Design & Bedrock Extraction Evidence | 0/TBD | Not started | - |
| 4. Reviewer-Ready Submission & Handoff | 0/TBD | Not started | - |
