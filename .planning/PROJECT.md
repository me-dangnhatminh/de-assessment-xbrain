# Xbrain Data Engineer Assessment POC

## What This Is

This repository is a submission-grade proof of concept for the August 2026 Xbrain Data Engineer (AI / Knowledge Engineering) assessment. It delivers a local Python data pipeline and operational knowledge base for the fictional Sao Do Finance customer, together with the required AI-proficiency artifacts and reproducible evidence that every result was verified.

The finished repository is intended for Xbrain and TechX evaluators. It must demonstrate sound judgment, an honest and traceable working process, and the ability to explain every submitted line—not merely produce plausible-looking outputs.

## Core Value

Every claimed result must be reproducible, source-grounded, and understandable enough for the candidate to defend in a technical interview.

## Requirements

### Validated

- [x] Build a local Python pipeline that ingests `app_logs_7days.jsonl`, detects data-quality issues, applies explicit validation and cleaning decisions, and preserves the original input unchanged. — Validated in Phase 1: Auditable Log Pipeline & Analysis
- [x] Store the cleaned logs in a justified structured format and produce executable SQL or pandas analysis with recorded results for all four customer questions. — Validated in Phase 1: Auditable Log Pipeline & Analysis
- [x] Document how many records were rejected or repaired, grouped by data-quality issue and supported by pipeline evidence. — Validated in Phase 1: Auditable Log Pipeline & Analysis
- [x] Build a searchable knowledge base from all eight supplied operational documents after applying the provided chunking and RAG-evaluation guidance. — Validated in Phase 2: Version-Aware Knowledge Base & Evaluation
- [x] Preserve source, section, version, effective date, and ownership metadata so retrieved content is attributable and version conflicts can be resolved deterministically. — Validated in Phase 2: Version-Aware Knowledge Base & Evaluation
- [x] Identify the conflicting documents and ensure retrieval favors the current effective version without erasing historical provenance. — Validated in Phase 2: Version-Aware Knowledge Base & Evaluation
- [x] Create ten knowledge-base evaluation questions spanning direct lookup, multi-source synthesis, version traps, and out-of-scope refusal, each with an expected answer, source, and pass/fail criteria. — Validated in Phase 2: Version-Aware Knowledge Base & Evaluation
- [x] Execute and report at least three knowledge-base evaluation cases, separating retrieval quality from answer groundedness. — Validated in Phase 2: Version-Aware Knowledge Base & Evaluation
- [x] Write an English, one-page-or-shorter SOP covering document additions and revisions, re-indexing, validation, frequency, ownership, and approval. — Validated in Phase 2: Version-Aware Knowledge Base & Evaluation

### Active

- [ ] Produce an AWS daily-pipeline architecture diagram and an English explanation of no more than one page, including data flow, service choices, IAM considerations, and explicit uncertainties.
- [ ] Maintain an English `AI_WORKLOG.md` with 8–15 meaningful entries recording the task, prompt, output assessment, verification, and corrections for AI-assisted work that affects the submission.
- [ ] Write an English, one-page-or-shorter review that identifies every incorrect or misleading claim in the supplied AI response, explains the correction, and cites authoritative verification sources.
- [ ] Design an English, two-page-or-shorter prompt for extracting free-text log messages into a strict JSON schema, with explicit missing/ambiguous-value behavior and no unsupported inference.
- [ ] Create five representative prompt test cases from the supplied logs, including at least one difficult or ambiguous case, with expected structured outputs.
- [ ] Define a measurable evaluation method for running the extraction prompt over 3,000 real log lines, including hallucination detection and human-review thresholds.
- [ ] Run all five extraction-prompt test cases through Amazon Bedrock and report the raw outcomes, comparisons with expected outputs, and corrective observations.
- [ ] Provide an English root README with project overview, setup, commands for every part, outputs, design decisions and rationale, limitations, and unfinished or uncertain items.
- [ ] Preserve genuine incremental Git history throughout implementation and prepare the repository for GitHub submission plus a ZIP backup.

### Out of Scope

- Deploying the proposed daily data pipeline to a live AWS environment — the assessment requests an on-paper design; only the Bedrock prompt trial requires live AWS access.
- Building a production-grade conversational UI or enterprise RAG platform — the required deliverable is a small, inspectable knowledge base with retrieval and evaluation evidence.
- Modifying the supplied raw logs, operational documents, assessment briefs, or reading pack — source artifacts remain immutable inputs.
- Adding unsupported operational facts to compensate for missing documentation — unknown or out-of-scope questions must be identified rather than answered speculatively.
- Optimizing for large-scale distributed processing — the seven-day POC should favor a simple implementation that runs correctly and is easy to explain.

## Context

- The assessment simulates a two-day customer POC for Sao Do Finance and is graded primarily on reasoning, process, learning speed, verification discipline, and honesty.
- Source requirements are in `docs/onboard/01_Domain_POC.md` and `docs/onboard/02_AI_Proficiency.md`.
- The data pack is under `docs/onboard/datapack/`: seven days of JSONL logs covering five systems, eight operational documents, and two required readings on chunking and RAG evaluation.
- The log data is intentionally dirty. Cleaning behavior must be discovered from the file, quantified, justified, and encoded rather than handled manually.
- The document collection intentionally contains at least one version conflict. Freshness and version metadata are functional requirements, not documentation-only concerns.
- The knowledge-base evaluation must distinguish retrieval failure from generation failure and must penalize answers that cite obsolete versions or introduce unsupported claims.
- AI use is explicitly allowed, but every material use must be logged and every output must be independently checked before inclusion.
- Interviewers may probe any code or document line. Simplicity and explainability take priority over impressive but opaque tooling.

## Constraints

- **Timeline**: Two days — prioritize a complete, runnable, well-evidenced submission over unnecessary architectural complexity.
- **Implementation**: Python and local execution for the data pipeline — AWS deployment is not required.
- **Cloud AI**: Amazon Bedrock — AWS credentials, region access, and an enabled model are available for the five-case live prompt trial.
- **Language**: English throughout — README, supporting documents, code comments, reports, and evaluation artifacts.
- **Length**: AWS explanation and AI-response review are each no more than one page; the structured-extraction prompt task is no more than two pages.
- **Data integrity**: Supplied source files must remain unchanged — generated datasets, indexes, and reports live in project output locations.
- **Evidence**: All reported results must be regenerable through documented commands and backed by tests, queries, evaluation records, or authoritative sources.
- **Submission shape**: Preserve the required top-level deliverable areas: `pipeline/`, `kb/`, `design/`, `sop/`, `AI_WORKLOG.md`, and the root `README.md`.
- **Version control**: Commit along the real implementation progression rather than squashing all work into a final commit.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Complete every mandatory requirement and the optional live LLM trial | The submission should demonstrate the full expected AI-proficiency bar rather than leave bonus evidence theoretical | — Pending |
| Use English for all submitted artifacts | Creates a consistent, reviewer-friendly repository and exceeds the minimum English-only README requirement | — Pending |
| Use Amazon Bedrock for the five-case extraction-prompt trial | Keeps the live AI evaluation within the selected AWS ecosystem and available account access | — Pending |
| Keep the pipeline local-first and AWS deployment conceptual | Matches the brief and protects the two-day scope while still demonstrating cloud architecture judgment | — Pending |
| Treat source files as immutable inputs | Ensures cleaning and knowledge-base behavior are reproducible and auditable | — Pending |
| Prefer simple, explainable components over unnecessary sophistication | The assessment explicitly prioritizes working code, decisions, and understanding over complex tooling | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-12 after Phase 2 completion (Version-Aware Knowledge Base & Evaluation — 5/5 verified)*
