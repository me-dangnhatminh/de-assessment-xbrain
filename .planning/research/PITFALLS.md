# Domain Pitfalls: Xbrain Data Engineer Assessment POC

**Domain:** Submission-grade, two-day data-engineering and knowledge-engineering proof of concept
**Researched:** 2026-08-11
**Overall confidence:** HIGH for assessment-specific risks; MEDIUM for current Amazon Bedrock/AWS runtime behavior.

## How to Use This Register

This is not a production-risk catalogue. It prioritizes failures that would make this specific submission indefensible: a reviewer cannot rerun a claim, cannot trace it to an immutable source, sees a stale policy presented as current, or concludes that AI was used without verification. Each phase below has an owner so mitigations are planned instead of left to a final-day README edit.

**Suggested ownership phases**

1. **Evidence foundation** — source inventory, repository conventions, reproducibility contract, and work-log process.
2. **Deterministic log pipeline** — ingest, validation, repairs/rejects, structured output, analyses, and tests.
3. **Version-aware KB and evaluation** — document registry, chunks/index, retrieval, answer evidence, and SOP.
4. **AWS design and Bedrock extraction trial** — review, bounded architecture, prompt/schema, live runs, and security.
5. **Submission audit** — clean-room rerun, page-count checks, evidence review, README, ZIP, and honest handoff.

## Critical Pitfalls

### 1. Silent data loss or a non-idempotent cleaning run

**What goes wrong:** The script reads the supplied JSONL, drops malformed/unknown records without a row-level record, overwrites the input, or yields different cleaned data on a second run. A common variant is silently coercing an invalid timestamp/level to a plausible value and then counting it as clean.

**Why it happens:** Cleaning is treated as a convenience step rather than a set of explicit, testable business decisions. In a two-day rush, a dataframe's default parsing/drop behavior is accepted without checking what disappeared.

**Consequences:** The required rejected/repaired count cannot be defended; error-rate and top-error results can be wrong; raw evidence may be irreversibly changed. Re-running after a partial failure can duplicate records or change repairs, making the submission fail its central reproducibility claim.

**Prevention:** Preserve the supplied path as read-only in practice; stream each line with `source_line_number` and raw-line SHA-256; write only to project outputs. Classify every input exactly once as `accepted`, `repaired`, or `rejected`; give each issue an explicit code, original value, action, and reason. Make the final dataset a deterministic replacement (or an atomic temp-to-final write), and test that two fresh runs produce the same row counts, issue summary, content hash, and analyses.

**Early detection:** Before any analysis, reconcile `total physical lines = parse rejects + parsed candidates`; then reconcile `parsed candidates = accepted + repaired + validation rejects`. Run the pipeline twice from a clean generated-output directory and compare manifest hashes. A missing raw-input hash, duplicate source line number, or unexplained count difference is a release blocker.

**Owner:** Phase 1 defines the manifest/ledger contract; Phase 2 implements and proves it. **Confidence: HIGH** (assessment explicitly requires immutable input, discovered cleaning decisions, and counts by issue).

### 2. Weak data-quality accounting that cannot support the fourth customer answer

**What goes wrong:** A report says “N records were cleaned” but does not distinguish malformed JSON, missing field, invalid enum, timestamp issue, duplicate, and repair. Totals are calculated after filtering, or repair and rejection are mixed together.

**Why it happens:** Quality is reported as a final aggregate instead of emitted as a first-class pipeline artefact. The definition of “fixed” versus “discarded” is never written down.

**Consequences:** The fourth required question is answered vaguely; reviewers cannot reproduce the numbers or judge whether a repair was appropriate. It also hides whether the pipeline selectively removed inconvenient errors.

**Prevention:** Produce a machine-readable quality summary plus a compact human-readable report generated from the same ledger. Define issue codes and a mutually exclusive disposition taxonomy. Keep examples of each observed issue (redacting only if required), with source-line references. Make analysis scripts consume only the declared canonical cleaned dataset, never a notebook-only intermediate.

**Early detection:** A unit/integration test must assert the reconciliation equations above and expected issue-code counts from the fixed supplied file. Review the quality report against the ledger: every summary bucket must have rows, and every non-accepted row must be in one bucket only.

**Owner:** Phase 2. **Confidence: HIGH** (direct requirement; source inventory is small enough for complete reconciliation).

### 3. A confident but misleading anomaly claim

**What goes wrong:** The submission labels the largest daily ERROR count “anomalous” with no baseline, ignores incomplete-day/time-zone effects, or calls normal end-of-month `batch-report` behavior an incident. It may also mix all levels with `ERROR`, or use a visually striking chart in place of a stated rule.

**Why it happens:** “Which day is abnormal?” is mistaken for a request to find the maximum. The seven-day sample is too short to justify a sophisticated statistical claim, and supplied operating context is not consulted.

**Consequences:** The report overstates what evidence supports and may recommend the wrong operational response. This is especially damaging because the brief rewards honest uncertainty and tests whether the candidate can distinguish data from inference.

**Prevention:** State a simple, reproducible exploratory rule before inspecting the result (for example, daily ERROR count compared with the seven-day median and IQR, plus a labelled small-sample limitation). Report the raw daily series and denominator where relevant. Cross-check the interpretation with the documentation: monitoring thresholds are 15-minute error *rates*, not automatic proof that a daily count is an incident; `RUN-01` identifies expected month-end load behavior.

**Early detection:** Have the analysis command output the exact filter, daily aggregation, baseline calculation, and sample-size caveat. Require a reviewer checklist item: “Does this say observed outlier/signal rather than proven root cause?” If an anomaly rule is absent or changes after results are seen, mark it exploratory rather than a verified finding.

**Owner:** Phase 2, with final wording checked in Phase 5. **Confidence: HIGH** (brief and supplied operational documents); do not claim causal diagnosis from these logs alone.

### 4. Retrieval presents obsolete backup policy as current truth

**What goes wrong:** A lexical or embedding search retrieves `POL-01` v1.0 alongside v2.0 and the answer uses the old 22:00/7-day/on-premises/no-approval rules—or merges both versions into a fabricated compromise. Deleting v1.0 avoids the symptom but destroys historical provenance.

**Why it happens:** Version/effective-date metadata is omitted, stored only in chunk text, or not used in ranking/answer selection. “Newest file modification time” is substituted for an explicit effective-version rule.

**Consequences:** The KB fails a deliberately planted version trap and gives unsafe operational advice. A reviewer cannot see why one source won or trace the prior policy.

**Prevention:** Build a document registry with document ID, version, issue/effective date, owner, supersedes/status, content hash, and source path. Preserve all versions. Filter or strongly demote superseded chunks by default, then show the selected effective source in the answer citation; make historical retrieval an explicit mode. Encode and test the known `POL-01` v2.0 superseding v1.0 relation rather than relying on filename sorting.

**Early detection:** A pre-index inventory must list both `POL-01` versions and their relationship. Add a version-trap eval before polishing retrieval: answers must cite v2.0 and exactly reject v1.0 values. Inspect the top-k result list as well as the answer; v1 may appear for audit, but must not win normal current-policy answering.

**Owner:** Phase 3. **Confidence: HIGH** (the supplied policy says v2.0 replaces the prior version; reading pack requires version/date/owner metadata and deterministic conflict handling).

### 5. Chunk granularity destroys operational meaning

**What goes wrong:** Fixed chunks split a restart precondition from its action, separate a table header from its thresholds, or create huge whole-document chunks that bury a direct answer. A universal “4,000 tokens is best” rule is copied into the design despite the assessment’s explicit warning against it.

**Why it happens:** Chunking is selected by convention or framework default, not from the question types and document structures. Tables, ordered SOP steps, version headers, and citations are not carried with chunks.

**Consequences:** Retrieval misses direct lookup, generated answers omit a critical constraint (for example, queue must be zero before a payment-api restart), and citations become too vague to verify.

**Prevention:** Begin with explainable structure-based chunks: document header/version metadata plus one coherent heading, ordered procedure, or table section per chunk. Keep title/section path and a stable chunk ID. Split oversized sections only at sentence/row boundaries with a documented small overlap; do not separate ordered steps from the condition they depend on. Use the ten planned questions to tune only if an observed retrieval failure warrants it.

**Early detection:** Generate a chunk inventory with word/token length, heading, first/last text, and table/step flags. Manually inspect every chunk in this eight-document corpus. Retrieval tests must cover a table threshold, a multi-step procedure, a multi-source synthesis, and the version trap.

**Owner:** Phase 3. **Confidence: HIGH** (supplied chunking reading); the precise size threshold is intentionally a project decision, not an external fact.

### 6. Evaluation leakage and self-confirming KB evidence

**What goes wrong:** Eval questions are written after seeing search results, expected answers merely restate the model’s output, the same question is repeatedly tuned until it passes without recording changes, or all ten cases are easy direct lookups. A three-case “demo” is then presented as proof of overall quality.

**Why it happens:** The team confuses a demo with an evaluation and has no fixed evaluation fixture or scoring rubric. Time pressure rewards visible pass rates over a falsifiable test.

**Consequences:** Retrieval quality is overstated, planted failures are missed, and subsequent index changes cannot be compared fairly. Evaluators can quickly spot that out-of-scope and obsolete-version behavior was never really tested.

**Prevention:** Write and version the ten fixtures before final retrieval tuning: question ID/type, expected document/section/version, required facts, disallowed obsolete facts, and pass/partial/fail rule. Include direct lookup, multi-source synthesis, version trap, and explicit out-of-scope refusal as required by the reading pack. Record every run against fixture and index hashes; treat changed fixtures as a new version, not a silent overwrite.

**Early detection:** Check the fixture table before implementing the answer layer: all four categories present; no answer contains untraceable content; expected sources predate results. The run report must show top-k retrieved chunks and score all ten fixtures even if only three are executed end-to-end with answer generation.

**Owner:** Phase 3, audited in Phase 5. **Confidence: HIGH** (assessment reading prescribes the categories and predeclared source/criteria).

### 7. Confusing retrieval success with grounded answer quality

**What goes wrong:** The correct chunk is in top-k, so the case is marked pass even if the answer invents a detail, omits a qualification, cites the old policy, or refuses incorrectly. Conversely, an answer that happens to be correct by model prior knowledge masks a retrieval miss.

**Why it happens:** Only one binary “answer correct” score is recorded. The retrieval trace and claim-by-claim answer comparison are not saved.

**Consequences:** The team cannot tell whether to improve chunking/ranking, answer instructions, or source citation. More importantly, the submission directly misses a stated grading distinction.

**Prevention:** Score two independent fields per case: **retrieval hit** (the expected effective chunk is in a declared top-k) and **groundedness** (each answer claim is entailed by cited effective chunks; no unsupported/obsolete claim). Add answer completeness and citation correctness as separate notes. An out-of-scope case passes only when it declines to invent an answer and says the corpus lacks the information.

**Early detection:** Require a scorecard with question, expected source/version, retrieved IDs/ranks, answer, citations, claim-level evidence, retrieval verdict, groundedness verdict, and reviewer. A blank provenance field or a single combined score fails the evidence review.

**Owner:** Phase 3. **Confidence: HIGH** (supplied RAG-evaluation reading explicitly distinguishes these failure locations).

### 8. Treating Bedrock output as parsed fact

**What goes wrong:** The runner assumes every completion is valid JSON; strips code fences/trailing prose and silently “repairs” it; coerces unsupported extracted fields; or sends model output into the cleaned log dataset/KB. A syntactically valid object is mistaken for a semantically faithful extraction.

**Why it happens:** A strict prompt is mistaken for a validator, or structured-output support is assumed without checking the chosen model/API. Error and refusal paths are not retained as evidence.

**Consequences:** The five-case trial appears cleaner than it was, hallucination/missing-value behavior is hidden, and the POC loses its separation between deterministic data engineering and experimental AI extraction.

**Prevention:** Define a local JSON Schema and deterministic comparison rules first. Use Bedrock Structured Outputs only after confirming the selected model/API supports it; AWS says unsupported schema features fail validation with HTTP 400, so keep the schema deliberately small and preflight it. Independently validate every received object locally, preserve raw text/response and validation error, and represent unknown/ambiguous data explicitly as `null`/a controlled enum rather than inferred values. Keep the trial read-only: it must never change canonical pipeline or KB data.

**Early detection:** Run all five immutable fixtures, including an ambiguous case, through: API success check → raw-response capture → JSON parse → schema validation → field comparison → human observation. Any parser repair, schema failure, extra key, invalid enum, or unsupported inference is a recorded failed/partial case—not a hidden retry.

**Owner:** Phase 4. **Confidence: MEDIUM** for current Bedrock Structured Outputs behavior; HIGH for the assessment’s requirement to report raw outcomes, comparisons, and corrections.

### 9. Bedrock trial is non-reproducible because model, Region, endpoint, and parameters drift

**What goes wrong:** The submission reports “tested with Bedrock” but omits the model/inference-profile ID, Region, API surface, SDK version, prompt/schema version, temperature, max tokens, timestamp, and request outcome. A hard-coded model ID later fails in the candidate’s Region, or a selected endpoint does not support the structured-output feature used.

**Why it happens:** Bedrock is treated as one uniform model rather than a service with model-specific capabilities, regional availability, access/permission conditions, and nondeterministic output. Results are copied from a console rather than produced by a runner.

**Consequences:** The live-trial claim cannot be rerun or explained. A configuration failure consumes the final hours; worse, rerunning can produce different output with no ability to diagnose the change.

**Prevention:** Provide a small runner that reads non-secret configuration from environment variables, performs an explicit preflight, and fails loudly with actionable diagnostics. Preflight the selected model/inference profile in the target Region and its Converse/structured-output compatibility; AWS documents that parameters are model-dependent and that cross-Region profiles can route among destination Regions. Pin the boto3 version, use a fixed low-temperature setting only where supported, and persist a run manifest with all non-secret configuration, prompt/schema hashes, fixtures hash, UTC timestamp, raw outcome, and result status. Never promise deterministic model text; report the single observed trial and its limitation.

**Early detection:** Run a one-case connectivity/schema smoke test at the start of Phase 4, then run all five cases through the same script. Check that manifest fields are complete before declaring a result. Re-run one fixed case only to demonstrate/configure variability handling, labelling any difference rather than averaging it away.

**Owner:** Phase 4, with manifest/replay check in Phase 5. **Confidence: MEDIUM** (current AWS documentation verifies model-parameter, endpoint, structured-output, and Region/profile variability; exact available model depends on the account at run time).

### 10. Credentials, customer-like data, or sensitive metadata leak into the repository

**What goes wrong:** AWS keys, bearer/API keys, `~/.aws` material, an `.env`, raw CLI debug output, account IDs, or unnecessary prompt payloads are committed or included in the ZIP. An architecture diagram grants broad production access to a POC role, contradicting `POL-02`’s least-privilege/separated-environment policy.

**Why it happens:** The live trial needs credentials and artifacts quickly, while evidence capture and secret handling are not designed together. “Private repo” is incorrectly treated as a security control.

**Consequences:** Immediate submission/security risk, potential key rotation and account incident, and a strong signal that the candidate did not understand IAM. It may also violate the supplied policy that an external POC uses masked data in a segregated environment.

**Prevention:** Use normal AWS credential-provider resolution/temporary credentials or a named local profile; never embed credentials in code or fixtures. Commit an `.env.example` with variable names only and ignore actual secrets. Minimize the runner IAM policy to necessary model invocation/read-only discovery actions, scope resources/conditions where practical, and describe least privilege plus CloudTrail/audit logging in the design. Redact any account identifiers from public evidence and scan both the tracked tree and ZIP before handoff.

**Early detection:** Run a secret scanner plus targeted `git grep` patterns for AWS key prefixes and variables; inspect `git status --ignored` for accidental `.env`/credential files; run the script with no embedded credentials to ensure it relies on the approved provider chain. A detected secret is a stop-ship event: revoke/rotate it, remove it from history through the approved process, and document the remediation.

**Owner:** Phase 1 establishes the guardrail; Phase 4 applies it; Phase 5 runs the final scan. **Confidence: HIGH** for assessment/POL-02 policy; MEDIUM for current AWS implementation guidance, which recommends temporary IAM credentials and warns against embedded keys.

### 11. Generated evidence cannot be regenerated or is mistaken for source truth

**What goes wrong:** Parquet, SQLite, reports, diagrams, test results, and Bedrock outcomes are created manually or from unversioned notebooks; required evidence is ignored by Git with no rebuild command; or rerunning an output overwrites the prior result without an input/config manifest.

**Why it happens:** Artefacts are organized by file type rather than provenance, and the final README is deferred. Generated artefacts look authoritative even though their source command and inputs are not captured.

**Consequences:** A reviewer cannot reproduce stated numbers, know whether the index matches the eight source documents, or distinguish a live Bedrock response from an edited transcript. This defeats the project’s core value even when code happens to work locally.

**Prevention:** Give each generated artefact a producer command, input paths/hashes, code revision/version, and output location. Commit compact, reviewable manifests, ledgers, eval scorecards, and report CSV/Markdown; regenerate bulky Parquet/SQLite through documented commands or commit them only if the repository policy says so. Separate immutable inputs, deterministic derived data, and nondeterministic Bedrock evidence. Include a clean-environment setup/run sequence in the root README.

**Early detection:** In a fresh clone or clean output directory, run documented commands in order and compare manifests/report hashes. Ensure every README result links to a generated file and that every generated file either has a committed manifest or a stated regeneration policy.

**Owner:** Phase 1 creates conventions; every feature phase supplies its manifest; Phase 5 performs the clean-room run. **Confidence: HIGH** (explicit evidence/reproducibility requirements).

### 12. Page limits are violated or met by removing the verification that earns credit

**What goes wrong:** The AWS explanation or AI-response review exceeds one page, the prompt exceeds two pages, or a last-minute compression deletes sources, assumptions, test behavior, and limitations. Rendered page count differs from Markdown/editor length because of font, image, table, or PDF conversion changes.

**Why it happens:** Page-constrained documents are drafted last and validated as text files rather than as the submitted rendering. The team tries to present every possible AWS/RAG option instead of one justified design.

**Consequences:** A mechanical requirement fails, or the work appears verbose and evasive rather than well reasoned. Source-free AWS assertions are especially risky because Task A specifically asks for verification sources.

**Prevention:** Start each constrained deliverable with a one-page/two-page outline and evidence budget: claim → rationale → source/uncertainty. Use one diagram only when it replaces prose. Prefer a compact decision table and explicit limitations over generic service descriptions. Preserve full technical evidence in runnable code/manifests/README, while the constrained document links to it.

**Early detection:** Generate the final PDF/print rendering early and check physical page count after every substantive edit. A Phase-5 checklist verifies: English, exact page cap, legible citations, diagram labels, and no assertion lacking a source or clearly labelled uncertainty.

**Owner:** Phase 4 drafts restricted AI/AWS documents; Phase 5 enforces render checks. **Confidence: HIGH** (explicit assessment limits).

### 13. Opaque AI-generated code or prose cannot be defended in interview

**What goes wrong:** A framework-heavy pipeline, copied AWS claims, or model-generated report is committed without the candidate understanding its control flow, assumptions, and errors. The worklog says “verified” but names no command, source, test, or correction.

**Why it happens:** AI is used to accelerate production but not paired with a deliberate review loop. Complexity is mistaken for sophistication despite an eight-document/one-week POC.

**Consequences:** The assessor can invalidate otherwise working output by probing a line the candidate cannot explain. It also creates incorrect claims such as universal chunk size, row-based Parquet, or Lambda for 30–45-minute work—the intentionally misleading claims in the supplied task.

**Prevention:** Prefer the smallest direct implementation: named Python validation functions, a transparent SQLite/FTS or equally explainable index, direct SQL, and a narrow Boto3 adapter. For every material AI-assisted change, record the task, meaningful prompt summary, output assessment, concrete verification, and correction in `AI_WORKLOG.md`. Keep 8–15 substantive entries, including rejected AI suggestions and errors found, then do a line-by-line explainability review of code and key documents.

**Early detection:** Require each PR/commit to be explainable without an assistant present: author can state inputs, outputs, failure behavior, and test evidence. Sample random functions/paragraphs during Phase 5 and ask the candidate to explain why it exists and what would falsify it. Empty or generic worklog fields fail this check.

**Owner:** Continuous from Phase 1 through 5; Phase 5 samples and audits. **Confidence: HIGH** (assessment explicitly grades verification, corrections, and interview explainability).

### 14. Manufactured-looking Git or worklog history destroys the honesty signal

**What goes wrong:** The repository ends with a single polished commit, commits are bulk-created with artificial timestamps/messages, AI-worklog entries are retrospectively invented, or history and artefact timestamps contradict each other. Conversely, necessary correction commits are squashed away, hiding genuine learning.

**Why it happens:** Version control is treated as packaging instead of a record of decisions. The candidate tries to optimize appearance rather than preserve the actual two-day progression.

**Consequences:** The assessment explicitly says it will inspect the two-day commit history. Fake-looking chronology makes every verification claim less credible and is more damaging than an honestly documented unfinished edge case.

**Prevention:** Commit naturally at meaningful completed increments: source inventory/conventions, pipeline validation, analysis evidence, KB registry/index, evaluation, AWS/Bedrock artefacts, and final audit. Use factual messages and retain corrective commits. Add AI worklog entries when the material AI-assisted activity occurs; include the failed output and correction where applicable. Do not fabricate timestamps, backfill fictional interactions, or rewrite public/shared history merely to make it prettier.

**Early detection:** Before submission, inspect `git log --stat --reverse`, commit dates, changed files, and worklog references. Confirm that manifests, reports, and Bedrock run timestamps can be reconciled with their producing commits (allowing clearly documented local uncommitted run time). Flag a final mega-commit, unexplained mass addition, or generic retrospective worklog entry for honest remediation in README—not cosmetic fabrication.

**Owner:** Continuous from Phase 1; Phase 5 performs chronology review. **Confidence: HIGH** (explicit assessment instruction and grading emphasis on honesty).

## Moderate Pitfalls

### 15. AWS architecture answer repeats planted misinformation or over-designs the POC

**What goes wrong:** The one-page design calls S3 Standard-IA universally cheapest/default, Parquet row-based, direct production-RDS polling every five minutes a standard approach, or 30–45-minute transforms suitable for Lambda. The opposite failure is drawing a sprawling enterprise platform that cannot be explained.

**Prevention:** Treat the supplied AI answer as a review test, not a template. Tie each service choice to a stated daily batch requirement and uncertainty: immutable/raw S3 staging, a suitable scheduled transform service (Glue for work beyond Lambda’s 900-second maximum), query/serving choice, observability, and least-privilege IAM. State what needs customer volume/SLA/cost confirmation instead of asserting a universal pattern.

**Early detection:** Trace each sentence in the design/review to an official AWS source or a clearly labelled assumption. Check the rendered one-page result and verify that it distinguishes conceptual AWS design from the local POC implementation.

**Owner:** Phase 4. **Confidence: MEDIUM** for current AWS service details; [Lambda timeout documentation](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html) directly verifies the 900-second maximum.

### 16. Scope creep crowds out mandatory evidence

**What goes wrong:** Time is spent on embeddings, a chat UI, distributed processing, deployment, semantic chunking, or a large evaluation framework before the four analyses, ten fixtures, three recorded KB cases, SOP, prompt tests, and README are complete.

**Prevention:** Make an evidence-first delivery checklist and implement the simplest inspectable choice that satisfies it. Record deferred improvements explicitly. The eight-document corpus makes a simple local, metadata-aware search defensible; sophistication earns no credit if it hides the required version/evaluation evidence.

**Early detection:** Daily checklist review: every active effort must map to a mandatory requirement or a documented risk reducer. If a feature has no verifiable deliverable by the end of the day, defer it.

**Owner:** Phase 1 prioritizes; all phases enforce; Phase 5 reports honest deferrals. **Confidence: HIGH** (project constraints and rubric emphasis).

## Minor Pitfalls

### 17. English and submission-shape drift

**What goes wrong:** Required English artefacts contain untranslated explanations, commands in README are stale, or mandated top-level areas (`pipeline/`, `kb/`, `design/`, `sop/`, `AI_WORKLOG.md`) are missing/renamed.

**Prevention:** Maintain a requirement-to-file matrix and generate/check commands directly from README. Keep Vietnamese only in immutable supplied sources; submission explanations, code comments, and worklog stay English as the project decision requires.

**Early detection:** Phase 5 walks the repository from the assessor’s perspective: clone, read README, run commands, locate every mandatory area, and review English/links.

**Owner:** Phase 5, with every phase adding its matrix row. **Confidence: HIGH** (project requirements).

## Phase-Specific Warnings

| Phase topic | Likely pitfall | Mandatory mitigation / acceptance signal |
|---|---|---|
| Evidence foundation | Starting code before fixing source identities and output conventions | Input SHA-256/source inventory, generated-output policy, requirement-to-file matrix, first genuine worklog entry. |
| Log ingestion and cleaning | Silent drop, duplicate rerun, mutation of supplied JSONL | Per-line ledger; reconciliation equations; deterministic double-run hash test; raw source untouched. |
| Log analysis | Calling the maximum day a proven anomaly | Versioned SQL/pandas output with explicit rule, raw series, denominator/context, and limitation. |
| KB registry and chunks | v1/v2 conflict handled by filename/text accident | Registry preserves both `POL-01` versions, explicit `supersedes` relationship, effective-status filter, chunk inventory review. |
| KB evaluation | Demonstration passes while generation invents facts | Ten predeclared fixtures; separate retrieval-hit and groundedness columns; top-k/citation trace; version and refusal cases. |
| AWS review/design | Compact document contains unverified universal claims | Claim-to-source/assumption trace; PDF page-count check; workload-specific service rationale and IAM boundary. |
| Bedrock prompt trial | JSON-looking model output accepted or wrong model/Region fails late | Day-start preflight; fixed fixtures/schema; raw outcome + local validation + comparison manifest; no secret capture. |
| Submission audit | Artefacts run only on author machine; history looks fabricated | Fresh-output rerun, secret scan, README command check, PDF render checks, chronological Git/worklog review, honest limitations. |

## Sources

### Primary project sources — HIGH confidence

- [Project requirements and constraints](../PROJECT.md)
- [Domain POC assessment brief](../../docs/onboard/01_Domain_POC.md)
- [AI Proficiency assessment brief](../../docs/onboard/02_AI_Proficiency.md)
- [Supplied chunking guidance](../../docs/onboard/datapack/reading/01_chunking_basics.md)
- [Supplied RAG evaluation guidance](../../docs/onboard/datapack/reading/02_rag_eval_basics.md)
- [Current and superseded supplied backup policies](../../docs/onboard/datapack/data/docs/POL-01_chinh_sach_backup_v2.md) and [v1.0](../../docs/onboard/datapack/data/docs/POL-01_chinh_sach_backup_v1.md)
- [Supplied monitoring guidance](../../docs/onboard/datapack/data/docs/GUIDE-01_giam_sat_he_thong.md) and [batch-report runbook](../../docs/onboard/datapack/data/docs/RUN-01_runbook_batch_report.md)
- [Supplied access policy](../../docs/onboard/datapack/data/docs/POL-02_chinh_sach_truy_cap.md)

### Current official AWS sources — MEDIUM confidence

- [Amazon Bedrock Structured Outputs](https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html) — supported schema subset, HTTP 400 on unsupported schemas, API/model support caveats.
- [Amazon Bedrock endpoints](https://docs.aws.amazon.com/bedrock/latest/userguide/endpoints.html), [model parameters](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html), and [inference-profile Regions/models](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html) — endpoint, model, parameter, and Region variability.
- [AWS Lambda timeout configuration](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html) and [AWS Glue job timeout](https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-jobs-trigger.html) — Lambda 15-minute maximum versus batch ETL job behavior.
- [AWS IAM security best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html), [secure access keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/securing_access-keys.html), and [Bedrock IAM integration](https://docs.aws.amazon.com/bedrock/latest/userguide/security_iam_service-with-iam.html) — temporary credentials, least privilege, and Bedrock authorization controls.

## What Might Still Need Phase-Specific Research

- The exact Bedrock model/inference-profile ID, available Region, account permissions, and Structured Outputs support can only be confirmed by the configured account at Phase 4 preflight; do not state them as fixed in research or README.
- The supplied logs must determine actual quality issue categories and any daily outlier result. This register defines the required method and evidence, not the empirical answer before pipeline execution.
- If the final selected local retrieval engine changes from an explainable lexical approach, rerun the fixed ten-fixture suite and document the new index’s deterministic-build behavior before claiming an improvement.
