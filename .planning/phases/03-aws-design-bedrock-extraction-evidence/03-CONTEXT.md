# Phase 3: AWS Design & Bedrock Extraction Evidence - Context

**Gathered:** 2026-08-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver three bounded AI-proficiency artifacts: (1) a conceptual AWS daily-pipeline architecture diagram plus ≤1-page English explanation, (2) a ≤1-page English review correcting the supplied misleading AI response, and (3) a ≤2-page structured-extraction prompt with five test cases, a measurable 3,000-line evaluation method, and a live five-case Bedrock trial with saved raw evidence. All artifacts must be credential-safe, source-grounded, and honest about uncertainties.

Phase 3 does NOT include: actual AWS deployment, running inference over all 3,000 lines, building a RAG/conversational system, modifying supplied inputs, or final submission assembly (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### AWS Diagram & Explanation
- **D-01:** Use Draw.io for the architecture diagram. Commit both `design/aws_daily_pipeline.drawio` (editable source) and `design/aws_daily_pipeline.png` (rendered export). No Mermaid, no Node/npm dependency.
- **D-02:** Diagram shows full daily flow with failure paths and IAM boundaries: daily source ingestion → raw S3 bucket → Glue ETL validation/transform → quarantine path (dead-letter S3 prefix for failed records) → curated S3 bucket → Glue Data Catalog → Athena query layer. Include IAM role boundary boxes (dashed groups), CloudWatch alerting/monitoring node, and mark uncertain design decisions with `?` annotations directly on the diagram.
- **D-03:** The ≤1-page English explanation lives in `design/aws_daily_pipeline.md`. It must explicitly distinguish what the POC implements locally vs. what the AWS design proposes conceptually. Cover service justifications, IAM least-privilege boundaries, failure/retry handling, and a dedicated "Uncertainties & Assumptions" section at the end.

### AI Response Review (Task A)
- **D-04:** The review lives in `design/ai_response_review.md` (≤1 page). Structure as a numbered list of claims, each with: the incorrect/misleading quote, what's wrong, why it's wrong, the correct replacement, and the verification source (AWS docs URL, supplied reading reference, or practical evidence).
- **D-05:** Must address ALL six misleading claims in the supplied AI response: (1) S3 Standard-IA as "default cheapest", (2) Glue reading directly from RDS production every 5 min, (3) Parquet described as "row-based", (4) Lambda for 30–45 min transforms, (5) fixed 4,000-token chunking as "always best", (6) no versioning needed for KB. Link corrections to authoritative sources.

### Structured Extraction Prompt (Task B)
- **D-06:** Extraction prompt covers ALL log levels (ERROR, WARN, INFO) — the brief says "trường message" generically and requires at least one "ca khó/mơ hồ" which likely involves a non-ERROR or multi-interpretation message.
- **D-07:** Flat JSON output schema: `{ "event_type": string, "component": string|null, "parameters": {string: string|number|null}, "confidence": "high"|"medium"|"low", "parse_status": "success"|"partial"|"failed" }`. Matches the brief's "loại lỗi, component liên quan, tham số." Missing or ambiguous values use `null` with `parse_status: "partial"` or `"failed"` — never fabricated.
- **D-08:** The prompt document (≤2 pages) lives in `design/extraction_prompt.md`. Contains: role definition, input contract (single message string), processing rules (including the no-fabrication rule), output contract (JSON schema), and handling of unparseable/ambiguous messages.
- **D-09:** Five test cases selected from supplied data covering: at least 2 ERROR patterns with clear parameters, 1 WARN or INFO pattern, 1 ambiguous/difficult case, and 1 edge case (e.g., a message that could be misinterpreted). Each test case includes the raw message and the expected JSON output.

### Bedrock Configuration & Preflight
- **D-10:** Configuration via `.env` (gitignored) with `.env.example` committed showing placeholder keys: `AWS_REGION`, `BEDROCK_MODEL_ID`, `BEDROCK_MAX_TOKENS`, `BEDROCK_TEMPERATURE`. Python reads via `os.environ`. No secrets, account IDs, or real values in committed files.
- **D-11:** Separate CLI preflight command (`python -m design.bedrock preflight`) that validates: Region reachability, model/inference-profile availability, Converse API support, and IAM permissions. Outputs structured JSON metadata to `design/output/preflight_result.json` and exits 0 (pass) or 1 (fail with diagnostic). The trial command refuses to run without a recent passing preflight.
- **D-12:** Fully configurable model via `BEDROCK_MODEL_ID` — no hardcoded default. Preflight validates the configured ID supports the Converse API. Works with both foundation model IDs (e.g., `anthropic.claude-3-haiku-...`) and cross-region inference profile ARNs.

### Bedrock Trial Execution
- **D-13:** Trial runs all 5 fixed cases sequentially with the configured model. For each case: send one Converse request, save raw response JSON to `design/output/responses/{case_id}_raw.json`, validate output against the schema locally, produce field-level expected-vs-actual comparison, and record pass/fail diagnosis.
- **D-14:** Save non-secret invocation metadata per case: model_id, Region, SDK version (`boto3.__version__`), prompt SHA-256, request timestamp, response latency, input/output token counts, and inference parameters used. Never log credentials, session tokens, or account identifiers.
- **D-15:** Deterministic re-report command (`python -m design.bedrock report`) that reads saved raw responses and regenerates comparisons and the summary report without making new paid API calls. Supports reviewers who cannot or choose not to re-run live inference.
- **D-16:** Record honest observations about model behavior: variability between runs (if temperature > 0), unsupported features, any failures or unexpected outputs, and suggested prompt improvements. These go in `design/output/trial_observations.md`.

### 3,000-Line Evaluation Method
- **D-17:** Ground truth for the evaluation method uses Phase 1's deterministic regex-based normalization outputs for ERROR messages (6 known patterns). For non-ERROR messages (~10 known templates), define expected field mappings from observed message patterns. This leverages verified existing work.
- **D-18:** Three-tier evaluation structure documented in the prompt file's evaluation section: (1) **Schema validity** — does output parse as valid JSON matching the defined schema? Target: 100%, automated. (2) **Field-level correctness** — per-field precision/recall against ground truth. Target: ≥95% for ERROR messages. (3) **Hallucination detection** — flag any output value not traceable to tokens in the input message. Target: 0% hallucination rate.
- **D-19:** Sampling strategy: stratified by message pattern (proportional to frequency in the 3,000 lines). Human-review triggers: all cases with `confidence: "low"`, all cases with `parse_status: "failed"`, and a random 5% sample of `"high"` confidence results for spot-checking.
- **D-20:** This is a METHOD DOCUMENT — it describes how to evaluate, not a live 3,000-line run. The brief asks "cách đánh giá" (evaluation method), not execution of 3,000 inferences.

### Agent's Discretion
- Exact file layout within `design/output/` for trial artifacts — flexible as long as paths are documented.
- Choice of which 5 specific log messages to use as test cases from the ~20 distinct patterns — planner selects to maximize coverage of error types, difficulty, and the "at least 1 ambiguous case" requirement.
- Wording and structure of the AI response review — flexible as long as all 6 claims are addressed with sources.
- Internal module layout of `design/` Python code — flexible as long as CLI entry points are documented.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Assessment Briefs (authoritative requirements)
- `docs/onboard/01_Domain_POC.md` — Section "Thiết kế AWS (trên giấy)" defines the diagram + explanation requirement; grading criteria
- `docs/onboard/02_AI_Proficiency.md` — Task A (AI review), Task B (extraction prompt + Bedrock trial), grading criteria, AI Work Log requirements

### Supplied AI Response to Review (Task A input)
- `docs/onboard/02_AI_Proficiency.md` §Yêu cầu 2 — Contains the full AI response with 6 embedded errors to identify and correct

### Source Data for Extraction Prompt
- `docs/onboard/datapack/data/app_logs_7days.jsonl` — 3,000 lines, 6 ERROR patterns, ~10 INFO/WARN patterns. Test cases MUST come from this file.

### Required Reading (inform AI review and KB versioning discussion)
- `docs/onboard/datapack/reading/01_chunking_basics.md` — Chunking strategies and design questions (relevant for reviewing the "4,000 token" claim)
- `docs/onboard/datapack/reading/02_rag_eval_basics.md` — RAG evaluation basics (relevant for reviewing the "no versioning" claim)

### Prior Phase Outputs (ground truth for extraction evaluation)
- `pipeline/normalize.py` — Phase 1's deterministic error normalization (6 error type patterns). Use as ground truth baseline for evaluation method.
- `pipeline/models.py` — Issue codes and normalization signatures

### Project & Requirements
- `.planning/PROJECT.md` — Core value, constraints (≤1 page, ≤2 pages limits, English, no credential exposure)
- `.planning/REQUIREMENTS.md` — RPRO-05, AWS-01–03, AIREV-01–03, AIEXT-01–10 requirement definitions
- `.planning/ROADMAP.md` §Phase 3 — Success criteria (5 items) and requirement mapping

### Technology Stack
- `.planning/research/STACK.md` §Boto3, §Amazon Bedrock — Converse API, preflight discovery, model selection guidance

### Prior Phase Context
- `.planning/phases/01-auditable-log-pipeline-analysis/01-CONTEXT.md` — Immutable-input, no-fabrication, explicit-evidence patterns
- `.planning/phases/02-version-aware-knowledge-base-evaluation/02-CONTEXT.md` — POL-01 version conflict (relevant for AI review claim #6)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline/normalize.py` — Deterministic regex-based ERROR message normalization with 6 known patterns. Directly reusable as ground truth for the extraction evaluation method.
- `pipeline/models.py` — Typed `dataclass` contracts and issue-code pattern. Reuse for extraction result models.
- `pipeline/__main__.py` — Stage-oriented CLI with `argparse`. Reuse pattern for `design/` CLI entry points (preflight, trial, report).
- `pipeline/integrity.py` — `sha256_file()` hashing, output-path authorization. Reuse for prompt SHA-256 and credential-safety checks.
- `kb/models.py` — Evaluation result models. Pattern reference for trial result structures.

### Established Patterns
- CLI modules use `python -m <package> <command>` entry points with argparse
- Evidence output uses structured JSON + human-readable Markdown report
- Deterministic reruns: same inputs → same outputs (applies to report regeneration from saved responses)
- No secrets in repo; gitignored local state only

### Integration Points
- New implementation belongs under `design/` (required top-level deliverable area)
- `.env.example` at repo root for Bedrock configuration
- `design/output/` for generated trial artifacts (gitignored raw responses, committed reports)
- Phase 1 `pipeline/normalize.py` provides ground truth data for evaluation method
- Phase 2 POL-01 version conflict provides concrete evidence for AI review claim #6

### Known Message Patterns (from data)
Six ERROR patterns: `ERR AuthTokenExpired uid=X`, `ERR ConnTimeout db-primary after Ns retry=N`, `ERR HTTP 502 upstream=payment-api path=/checkout`, `ERR NullPointer in ReportBuilder step=aggregate`, `ERR PaymentDeclined txn=X code=51`, `ERR SMTPConnRefused host=X`

Non-ERROR patterns: `Session created`, `User login success`, `Token refreshed`, `Balance check ok`, `Payment processed`, `Email sent`, `SMS sent`, `Slow login`, `Slow query`, `Retry 1/3`, `Queue depth high`, `Daily report job started/finished`, `Report row mismatch`, `Request completed`, `Response time`, `Clock sync failed`

</code_context>
