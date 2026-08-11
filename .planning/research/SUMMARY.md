# Project Research Summary

**Project:** Xbrain Data Engineer Assessment POC  
**Domain:** Submission-grade local data engineering and AI/knowledge-engineering POC  
**Researched:** 2026-08-11  
**Confidence:** MEDIUM

## Executive Summary

This is a two-day assessment submission, not a production data platform. The credible solution is a small, local-first Python project that turns immutable supplied inputs into independently reproducible evidence: a validated log pipeline answering four required customer questions, a version-aware searchable KB over all eight operational documents, and a bounded Bedrock structured-extraction trial. Reviewers should be able to run each slice independently, inspect the inputs, rules, outputs, and manifests, and understand every choice in an interview.

Use `uv`-managed CPython, explicit standard-library validation, DuckDB plus Parquet for analytics, and SQLite FTS5 with normal metadata columns for the KB. Keep the requested AWS daily pipeline as a clearly labelled conceptual design (S3, Glue, Catalog, Athena, IAM), rather than making cloud deployment a dependency. Use a thin direct Boto3 Bedrock adapter only for the five fixed prompt cases; model availability, Region, and Structured Outputs support must be preflighted in the actual account.

The dominant risks are silent data loss, stale-policy retrieval, unsubstantiated AWS/AI claims, late Bedrock configuration failures, and scope creep. Mitigate them with append-only quality and evaluation ledgers, deterministic current-version filtering that preserves history, source/assumption traces, early live preflight, fixed fixtures, manifests, meaningful incremental commits, and an evidence checklist. Defer every capability that does not improve a mandatory, reviewer-verifiable deliverable.

## Key Findings

### Recommended Stack

The recommended stack is intentionally narrow: one Python environment, embedded local engines, and direct APIs. This reconciles the research files' common recommendation to favor transparent, runnable components over frameworks. Pin declared dependencies and commit `uv.lock`; the lockfile, not a research-time version literal, is the reproducibility authority.

**Core technologies:**

- **CPython `>=3.12,<3.15` with `uv`**: one locked, documented local runtime; record the actual Python version and use `uv sync --locked`.
- **Python standard library**: streaming JSONL, named validation/repair rules, hashes, CLI, SQLite access, and JSON evidence without obscuring decisions in a framework.
- **DuckDB + Parquet**: transform accepted records and execute checked-in SQL for the four required analyses; Parquet is the clean analytic boundary, not an excuse for over-engineering.
- **JSON/JSONL ledgers and SHA-256 manifests**: capture source line, rule ID, original/normalized values, action, counts, input hash, configuration, and output paths.
- **SQLite FTS5**: heading-based chunk search using `bm25()` for the eight-document KB, while normal columns retain source, section, version, effective date, owner, status, and content hash.
- **Boto3 Bedrock Runtime / `Converse`**: a tiny configurable runner for the five live extraction cases; no LangChain, agent framework, or hard-coded model ID.
- **`pytest` + Ruff + Make/README commands**: deterministic tests, lint/format checks, and one-command-or-equivalent verification evidence.

Critical preflights: confirm FTS5 is available in the target Python build; discover an account-permitted, active Bedrock text model in the chosen Region that supports the selected API/features. Use `AWS_REGION` and `BEDROCK_MODEL_ID` environment variables and never commit credentials or a real `.env`.

### Expected Features

The table stakes are the assessment's required evidence, not optional product capabilities.

**Must have (table stakes):**

- Immutable, deterministic JSONL ingestion with explicit validation, narrow repairs/rejections, per-line ledger, source hashing, and row-accounting invariants.
- Clean structured dataset plus checked-in SQL/code and recorded results for all four customer analyses; anomaly language must be rule-based and cautious.
- A one-page-or-shorter conceptual AWS daily-batch diagram and English explanation covering flow, IAM, assumptions, and uncertainty.
- All eight documents inventoried and chunked by structure, with attributable metadata and deterministic current-versus-historical handling of the `POL-01` conflict.
- Ten predeclared KB evaluation fixtures, plus at least three recorded executions separating retrieval hit/miss from answer groundedness; include version traps and out-of-scope refusal.
- A short KB revision SOP, an English AI worklog with genuine verification/corrections, AI-response claim review, strict extraction prompt, five expected-output fixtures, 3,000-line evaluation method, and five recorded Bedrock trials.
- Reviewer-facing submission shape: required directories, runnable English README, explicit limitations, and genuine incremental Git history.

**Should have (trust-building differentiators, only after table stakes):**

- A compact evidence manifest and clean-output smoke check.
- Saved KB retrieval traces and an explicit demonstration that `POL-01 v2` wins normal current-policy queries while v1 remains discoverable as superseded history.
- Claim-to-source matrix for the AI review and an honest limitations register.

**Deliberate exclusions:**

- No deployed AWS pipeline, Terraform/CDK, direct production access, or streaming/distributed processing.
- No dashboard, conversational UI, enterprise RAG/agent framework, managed vector database, or embeddings unless the simple baseline demonstrably fails (which research does not indicate).
- No LLM-driven cleaning or claimed 3,000-line live batch inference; only deterministic cleaning plus an evaluation plan and five required live cases.
- No modification of supplied logs, documents, briefs, or reading materials; no invented operational facts or metadata.

### Architecture Approach

Build three isolated vertical slices sharing evidence conventions, not runtime dependencies: (1) `pipeline/` reads immutable JSONL, emits run-scoped Parquet, quality ledger, four analysis results, and manifest; (2) `kb/` inventories documents before heading-aware chunking, stores a rebuildable FTS index plus human-readable chunk manifest, and evaluates retrieval/groundedness separately; (3) `design/bedrock_trial/` loads fixed cases, preserves raw responses, validates locally against the schema, compares each field to expected output, and records non-secret invocation metadata. The root README is the entry point; `design/`, `sop/`, and `AI_WORKLOG.md` provide the constrained supporting artifacts.

**Major components:**

1. **Pipeline reader and quality rules** — source-preserving parsing, acceptance/repair/reject decisions, stable issue codes, and reconciliation counts.
2. **Dataset writer and analysis** — run-scoped Parquet plus only the four requested SQL analyses; results must derive from cleaned records, never raw/rejected rows.
3. **KB inventory, chunk/index builder, and retrieval policy** — provenance-first registry, structure-preserving chunks, active/effective filter before relevance ranking, cited results, optional history access.
4. **KB evaluation harness** — executable ten-case fixture suite with recorded ranks/chunk IDs, source/version expectations, retrieval and groundedness verdicts.
5. **Bedrock trial adapter** — preflight, fixed fixture execution, raw/evaluated evidence, and no pathway to mutate pipeline or KB outputs.
6. **Conceptual AWS target** — daily S3 raw landing, scheduled Glue validation/transform, quarantine and curated Parquet prefixes, Catalog/Athena, CloudWatch/SNS, and distinct least-privilege roles. It is a design artifact only.

**Key patterns:** immutable inputs and append-only run evidence; deterministic IDs/hashes and output ownership; inventory-before-indexing; version/freshness selection before text relevance; test fixtures as evidence contracts; local schema validation after any model response; configuration/secrets only through CLI/environment/provider-chain boundaries.

### Critical Pitfalls

1. **Silent data loss, mutation, or non-idempotent reruns** — retain line numbers/hashes and a per-record decision ledger; prove `input = accepted + rejected` under an explicit duplicate policy and verify a double run.
2. **Superseded policy wins retrieval** — preserve both `POL-01` versions, encode `v2` as active/effective, filter current documents before ranking, return versioned citations, and test the version trap.
3. **Reporting claims rather than evidence** — every result needs a producer command, source/config/code reference, manifest, and a README link; use source/assumption traces for AWS and AI review claims.
4. **Bedrock fails late or JSON-shaped output is trusted** — perform a one-case account/Region/model/API preflight early; persist raw outcomes and validate/compare locally without silent repair or retry masking.
5. **Scope creep and fabricated-looking process** — prioritize mandatory artifacts before improvements, maintain genuine 8–15-entry AI worklog and incremental commits, and run a final clean-room, page-limit, secret, English, and submission-shape audit.

## Implications for Roadmap

Based on the combined research, use the following five phases. They deliver vertical evidence early and reserve the only live external dependency for a bounded, preflighted phase.

### Phase 1: Evidence Foundation and Submission Contracts

**Rationale:** Every later claim depends on immutable inputs, deterministic output conventions, and clear mapping from requirement to evidence. Establish these before writing feature code so the two-day effort cannot drift into untraceable artifacts.

**Delivers:** `uv` project/lock and verification commands; repository layout; `.gitignore`/`.env.example`; source inventory and SHA-256 policy; output/manifest conventions; requirement-to-file matrix; initial genuine AI worklog entry; baseline tests/lint.

**Addresses:** Immutable-input delivery, reproducibility, required submission shape, and credible history.

**Avoids:** Source mutation, secret leakage, generated-output ambiguity, and scope creep.

### Phase 2: Deterministic Log Pipeline and Required Analyses

**Rationale:** The four customer answers and data-quality accounting are the core engineering proof and have no dependency on cloud or LLM access. Build this first vertical slice to obtain concrete, reproducible evidence quickly.

**Delivers:** Streaming validation/repair/reject rules, ledger, Parquet output, run manifest, row-conservation/idempotency tests, checked-in DuckDB SQL/code for all four analyses, and cautious result report.

**Addresses:** Cleaned data, issue counts, four analyses, and deterministic reruns.

**Avoids:** Silent drops, manual cleaning, raw/rejected-row contamination, and unsupported anomaly claims.

### Phase 3: Version-Aware Knowledge Base and Evaluation

**Rationale:** The KB depends on a correct source inventory and must solve the intentional version conflict before any evaluation can be trusted. SQLite FTS5 and heading-based chunks are sufficient and faster to explain than a vector/agent stack.

**Delivers:** Eight-document inventory, metadata/status registry, section-based chunks and SQLite FTS index, default active-version retrieval with explicit historical mode, ten fixtures, at least three scored runs with retrieval traces, and the KB update/re-index SOP.

**Addresses:** Searchable attributable KB, conflict resolution, evaluation, groundedness separation, and SOP requirements.

**Avoids:** Anonymous chunks, stale-policy answers, silently discarded history, invented metadata, and unverifiable RAG demonstrations.

### Phase 4: AWS Design and AI-Proficiency Evidence

**Rationale:** These artifacts are bounded but require careful authoritative verification; Bedrock is the sole account-dependent activity and must not block local deliverables. Start its connectivity/model preflight immediately when this phase starts.

**Delivers:** Conceptual daily AWS diagram and ≤1-page explanation; source-backed correction review of supplied AI claims; ≤2-page strict extraction prompt, five fixed cases, and 3,000-line evaluation method; Bedrock preflight plus five raw trial outcomes, parsed/schema/comparison evidence, observations, and non-secret manifests.

**Addresses:** AWS architecture/IAM, AI review, structured extraction, live trial commitment, and scalable evaluation method.

**Avoids:** Deploying the diagram, Lambda-for-long-ETL misinformation, unverified universal AWS claims, model/Region surprises, silently repaired model output, and credential exposure.

### Phase 5: Reproducibility, Submission Audit, and Honest Handoff

**Rationale:** The assessment evaluates process and explainability as closely as implementation. A focused audit turns individually complete slices into a reviewer-runnable submission without adding product scope.

**Delivers:** Root README with commands/outputs/decisions/limitations; evidence manifest; clean-output or fresh-clone verification; test/lint run; PDF/render page-limit checks; secret scan; repository/English/required-path audit; chronological Git/worklog review; GitHub/ZIP readiness.

**Addresses:** Runnable handoff, evidence visibility, constrained-document compliance, and genuine incremental history.

**Avoids:** Stale README commands, missing required artifacts, page-limit violations, leaked credentials, and cosmetic rather than honest remediation.

### Phase Ordering Rationale

- Phase 1 makes all subsequent work reproducible and protects immutable inputs/secrets.
- Phase 2 produces the required deterministic business evidence before optional or external work.
- Phase 3 follows the KB dependency chain: inventory and metadata → chunks/index → version policy → fixtures/evaluation → SOP.
- Phase 4 groups short, document-oriented AWS/AI work but keeps the Bedrock runner independent of the deterministic pipeline and KB; preflight occurs at the beginning, not at deadline.
- Phase 5 validates the whole submission as an evaluator would. No deployment, UI, vector stack, or other anti-feature should precede any of these phases.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 2:** Inspect the actual JSONL before finalizing quality rules, duplicate semantics, repair policy, and the evidence-backed daily anomaly criterion; research defines method, not empirical results.
- **Phase 3:** Inspect exact corpus metadata/heading structures and both `POL-01` versions while designing the status/effective-date parser; use the supplied chunking and evaluation readings as the governing implementation guide.
- **Phase 4:** Required targeted research/preflight. Validate the actual Bedrock model/inference-profile ID, Region, account permissions, API/Structured Outputs compatibility, and schema subset. Verify every AWS claim against current official documentation before constraining the final pages.

Phases with standard patterns (skip research-phase):

- **Phase 1:** Standard Python project setup, locked dependency workflow, hashes/manifests, and secret hygiene; follow the settled conventions above.
- **Phase 5:** Standard reproducibility, test/lint, page-render, secret-scan, and README audit practices; execution discipline matters more than new research.

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Stack | MEDIUM | Official vendor/library documentation supports the chosen minimal tools; exact resolved dependency versions and FTS5 availability need target-machine validation. |
| Features | HIGH | Assessment briefs, project scope, supplied readings, and corpus are governing primary sources. |
| Architecture | MEDIUM | Local boundaries are strongly supported by fixed constraints; AWS service and Bedrock feature availability remain account/Region/workload-specific. |
| Pitfalls | HIGH | Most are direct consequences of explicit integrity, evidence, page-limit, scope, and assessment-process constraints; current AWS specifics are MEDIUM. |

**Overall confidence:** MEDIUM-HIGH. The delivery strategy is high-confidence because it is anchored in the fixed brief; implementation details requiring external/account state remain deliberately uncommitted until verified.

### Gaps to Address

- **Actual log findings:** Derive issue codes, repair/reject counts, duplicate treatment, and daily anomaly result from the supplied JSONL; do not prestate them from research.
- **Bedrock availability:** At Phase 4 preflight, record the selected model/inference profile, Region, access state, supported API/features, SDK version, and request parameters. If Structured Outputs is unsupported, locally validate strict prompted JSON and report failures honestly.
- **Source metadata completeness:** Store absent owner/effective/status metadata as `null` with warnings rather than infer it; encode only verified supersession relationships.
- **Commit versus regenerate policy:** Decide in Phase 1 which compact evidence is committed and which bulky Parquet/SQLite/raw payloads regenerate, then state it in README/manifests.
- **Conceptual AWS assumptions:** Keep delivery SLA, late-arrival behavior, retention, PII classification, encryption/KMS, network boundaries, account IDs, and cost assumptions explicitly unresolved unless the brief supplies them.

## Sources

### Primary (HIGH confidence)

- [Project context and fixed constraints](../PROJECT.md)
- [Domain POC assessment brief](../../docs/onboard/01_Domain_POC.md)
- [AI Proficiency assessment brief](../../docs/onboard/02_AI_Proficiency.md)
- [Supplied chunking guidance](../../docs/onboard/datapack/reading/01_chunking_basics.md)
- [Supplied RAG evaluation guidance](../../docs/onboard/datapack/reading/02_rag_eval_basics.md)
- Supplied operational corpus, especially [current backup policy](../../docs/onboard/datapack/data/docs/POL-01_chinh_sach_backup_v2.md), [superseded backup policy](../../docs/onboard/datapack/data/docs/POL-01_chinh_sach_backup_v1.md), [access policy](../../docs/onboard/datapack/data/docs/POL-02_chinh_sach_truy_cap.md), and the monitoring/runbook documents.

### Authoritative technical sources (MEDIUM confidence for current availability/details)

- [uv projects and lockfiles](https://docs.astral.sh/uv/concepts/projects/layout/) and [locking/syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [DuckDB Python client](https://duckdb.org/docs/stable/clients/python/overview) and [Parquet support](https://duckdb.org/docs/stable/data/parquet/overview)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)
- [Boto3 Bedrock Runtime](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime.html), [Bedrock Converse](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html), [model/API compatibility](https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html), and [model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- [AWS IAM best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html), [AWS Lambda timeout](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html), and [AWS Glue jobs/workflows](https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-jobs-trigger.html)

---
*Research completed: 2026-08-11*  
*Ready for roadmap: yes*
