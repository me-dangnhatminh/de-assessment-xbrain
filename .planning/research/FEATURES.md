# Feature Landscape

**Domain:** Submission-grade data engineering and AI/knowledge-engineering assessment POC
**Researched:** 2026-08-11
**Overall confidence:** HIGH — the assessment brief and supplied reading pack are the governing requirements.

## Decision Rule

This is a two-day assessment, not a product discovery exercise. A feature is valuable only if a reviewer can run it, inspect its evidence, or trace it to an explicit decision. Prefer one simple path that regenerates a result over a sophisticated component whose behavior cannot be defended in interview.

## Table Stakes

Features reviewers should be able to find and verify. “Evidence” describes the observable proof, not extra product scope.

| Feature / capability | Why expected | Complexity | Reviewer-verifiable evidence |
|---|---|---:|---|
| Immutable-input, deterministic pipeline run | The brief requires original logs unchanged and results regenerable. | Med | One documented command starts from `app_logs_7days.jsonl`; generated data and reports are separated from inputs; rerunning produces the same quality counts and analysis results. |
| Explicit validation and cleaning policy | Dirty data is intentional; silent/manual cleaning does not demonstrate engineering judgment. | Med | Code plus a decision table for each discovered issue: detection rule, reject/repair action, rationale, and record count. Preserve rejected-record reason(s) or a reproducible audit report. |
| Structured cleaned dataset with rationale | The pipeline must transform and persist clean data, with a justified format. | Low | Output schema, selected format, write location, and concise explanation tied to the four analyses. |
| Four reproducible customer analyses | These are the required business answers: error-heavy service, daily error trend/anomaly, top three error types by service, and rejected/repaired records by issue. | Med | SQL or pandas source, generated result table(s), stated time window, and a short interpretation that does not overclaim anomaly detection. |
| Daily AWS design, bounded to one page | The assessment asks for an on-paper AWS design, data flow, IAM considerations, and explicit uncertainties. | Low | Diagram plus ≤1-page English explanation showing ingest, storage, transform/query, least-privilege IAM boundary, and assumptions/unknowns. No deployed cloud pipeline is required. |
| Inspectable KB over all eight supplied documents | The corpus and the two reading files make chunking, index choice, and traceability core requirements. | Med | Ingestion/chunk manifest proves all eight docs were processed; each chunk stores source document, section, version, effective/issue date, and owner where supplied. |
| Structure-based chunking with documented exceptions | The supplied reading recommends document-section chunks for operational/policy documents; fixed token size is not a universal answer. | Med | Chunking rules, chunk inventory, and a few representative chunks showing headings/procedure steps remain together. |
| Deterministic version/freshness handling | The corpus intentionally contains a conflict. `POL-01` v2 supersedes v1 and changes operational instructions. | Med | Version-selection rule and an audit-visible result: v2 is favored for current-policy answers while v1 remains discoverable as historical provenance. |
| Ten-question KB evaluation set | The brief explicitly demands ten questions, expected answers, sources, and pass/fail criteria. | Med | Machine-readable or tabular fixture with direct lookup, multi-source synthesis, version trap, and out-of-scope/refusal cases; expected source section and current-version expectation are predeclared. |
| At least three executed KB evaluations | A question list alone does not prove retrieval behavior. The reading requires distinguishing retrieval failure from groundedness failure. | Med | Run report with query, top retrieved chunks/sources, retrieval hit/miss, answer, groundedness judgment, and result/diagnosis. |
| KB update/revision SOP (≤1 page) | Required handover artifact and essential for preventing stale answers. | Low | English SOP identifies intake, metadata/version validation, approval/owner, re-indexing, regression eval, cadence, and rollback/history handling. |
| Credible AI work log | The AI assessment requires 8–15 material uses of AI, including verification and corrections. | Low | `AI_WORKLOG.md` entries record task, meaningful prompt summary, output assessment, independent verification, and edits made. Include at least one detected AI error when genuine. |
| AI-response review with source-backed corrections | The brief requires every misleading claim identified and corrected, within one English page. | Med | Claim-by-claim review links each correction to AWS documentation or the supplied readings; it separates “wrong,” “overgeneralized,” and “context-dependent.” |
| Strict extraction prompt, test fixtures, and 3,000-line evaluation method | The AI task requires schema-first extraction, ambiguity handling, five chosen real messages (including a difficult one), and a measurable scale-up plan. | Med | ≤2-page English prompt; explicit null/unknown/refusal behavior; five input/expected JSON fixtures; metrics, hallucination checks, and a human-review threshold for 3,000 lines. |
| Root README, package shape, and genuine history | Submission instructions require a runnable English handoff, required directories, GitHub/ZIP readiness, and incremental commits. | Low | README covers setup, commands, outputs, decisions, limitations, and unfinished/uncertain work; repository contains `pipeline/`, `kb/`, `design/`, `sop/`, `AI_WORKLOG.md`; Git history reflects incremental implementation. |

## Differentiators

These make the required work easier to trust. They should be added only after the table stakes are complete.

| Differentiator | Value proposition | Complexity | Notes |
|---|---|---:|---|
| One-command evidence manifest | Turns scattered output into an auditable submission: input path/hash, run timestamp, row counts, quality counts, output paths, and command/version information. | Med | Do not imply bit-for-bit reproducibility if timestamps or LLM calls vary; record those sources of variance. |
| Automated rerun/smoke check | Demonstrates the pipeline actually executes from a clean checkout rather than only producing committed artifacts. | Low | Check exit status, expected output existence, and internally consistent record accounting—not brittle hard-coded business answers. |
| KB eval harness with saved retrieval traces | Makes retrieval versus groundedness diagnosable and lets the same ten fixtures run after document revisions. | Med | Save query, ranked chunk IDs, active/historical version state, answer, and scorer notes; manual groundedness scoring is appropriate for this small POC. |
| Explicit conflict demonstration | Shows the evaluated backup query returns v2’s 23:30/30-day/cloud-encrypted/approval policy and labels v1 as superseded. | Low | This is more persuasive than merely stating that version metadata exists. |
| Live Amazon Bedrock run report for all five prompt cases | The brief marks a live LLM trial as optional, but the project decision commits to it; it supplies concrete AI-proficiency evidence. | Med | Record model ID, region, prompt/payload version, parameters, timestamp, raw response, JSON-validity check, expected-vs-actual comparison, and observed correction. Never record credentials or sensitive account identifiers. Amazon Bedrock’s `InvokeModel` API is model-specific and uses JSON request/response bodies. **Confidence: MEDIUM** (official AWS documentation verified through web lookup). |
| Claim-to-source matrix for the AI review | Lets a reviewer quickly audit coverage of every planted bad claim and prevents citations from becoming decorative. | Low | Keep the final review within its one-page limit; the matrix can be compact or placed in supporting notes if necessary. |
| Honest limitations register | Makes assumptions, non-deployments, incomplete validation, model variability, and known KB gaps explicit. | Low | The briefs explicitly reward uncertainty disclosure. This is a trust feature, not an apology. |

## Anti-Features

Deliberately avoid these additions; they consume the two-day budget while weakening explainability or violating the brief’s scope.

| Anti-feature | Why avoid | Do instead |
|---|---|---|
| Deploying AWS pipeline infrastructure | Explicitly out of scope; it creates credentials, cost, and operations risk without meeting a required artifact. | Produce the diagram and bounded explanation, clearly marking assumptions. |
| Conversational UI, agent framework, or enterprise RAG platform | The deliverable is a small inspectable KB with retrieval/evaluation evidence, not a polished assistant. | Provide a CLI/script or small evaluation runner that exposes sources and retrieved chunks. |
| Opaque vector stack “because RAG” | The brief accepts options from SQLite full-text search to embeddings and values justification over tooling. An unnecessary dependency is hard to explain and validate. | Use the simplest retrieval mechanism that demonstrably retrieves section-level chunks and exposes rankings/sources. |
| LLM-based cleaning or batch extraction of all logs | The base pipeline must make explicit validation decisions; the AI task requires only five live tests and a method for evaluating 3,000 lines. | Keep deterministic parsing/cleaning for the POC; document the 3,000-line sampling, hallucination detection, and review threshold without pretending it was run. |
| Dashboard, streaming ingestion, or distributed processing | None is requested, and seven days of logs fit a local Python workflow. | Commit clear tables/reports and an AWS daily-batch design. |
| Modifying raw logs, docs, briefs, or readings | Violates data integrity and destroys reproducibility. | Treat supplied files as read-only; emit all derived data, indexes, reports, and fixtures elsewhere. |
| Silently discarding historical KB versions | Fails the provenance requirement and makes conflicting answers impossible to audit. | Retain historical chunks with an explicit inactive/superseded status and filter/rank them deterministically for current answers. |
| Invented answers or metadata | Unsupported operational claims and fabricated owner/effective-date values directly undermine groundedness. | Return out-of-scope/unknown where the corpus is silent; distinguish missing metadata from an inferred value. |
| Synthetic AI worklog or unverified AI prose/code | The interview may probe any submitted line; a polished but non-defensible artifact is a serious red flag. | Log real material uses and independently run/check every included output. |

## Feature Dependencies

```text
Immutable source inputs
  → deterministic ingest/validation/cleaning
  → structured clean dataset + quality accounting
  → four analyses + reproducible report

Supplied documents + metadata extraction
  → section-preserving chunks + index
  → version/freshness policy
  → ten-question eval fixture
  → retrieval traces + groundedness assessment
  → revision SOP and regression reruns

Extraction schema + ambiguity policy
  → five expected-output fixtures
  → Bedrock trial report (project commitment)
  → 3,000-line evaluation plan

All artifacts + decisions + run commands
  → README / evidence manifest / AI worklog / incremental Git history
```

## MVP Recommendation

Prioritize in this order:

1. A local, deterministic pipeline that produces clean structured data, complete quality accounting, and all four answers.
2. A small section-based KB with metadata, a transparent current-version rule, ten evaluation fixtures, and three recorded evaluation runs.
3. Complete reviewer-facing evidence: README, AWS paper design, SOP, AI worklog, AI-response review, and structured extraction prompt/tests.
4. The five-case Bedrock trial and its raw evidence report, because this project has explicitly committed to the optional assessment bonus.

Defer: deployment, UI, streaming, large-scale batch inference, dashboarding, and semantic/agentic retrieval. They are not needed to prove the assessment’s intended skills.

## Sources

- **HIGH:** [Project requirements](../PROJECT.md), especially Active requirements, Constraints, and Out of Scope.
- **HIGH:** [Domain POC assessment brief](../../docs/onboard/01_Domain_POC.md) and [AI Proficiency brief](../../docs/onboard/02_AI_Proficiency.md).
- **HIGH:** [Chunking guidance](../../docs/onboard/datapack/reading/01_chunking_basics.md) and [KB evaluation guidance](../../docs/onboard/datapack/reading/02_rag_eval_basics.md).
- **HIGH:** Supplied operational corpus, particularly `POL-01_chinh_sach_backup_v1.md` and `POL-01_chinh_sach_backup_v2.md`, which define the intentional version conflict.
- **MEDIUM:** [Amazon Bedrock `InvokeModel` API reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModel.html) and [Invoke API user guide](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-api.html), externally verified on 2026-08-11.
