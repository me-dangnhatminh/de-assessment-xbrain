# AI Worklog

This document is a chronological digest of AI-assisted work across the assessment. Each entry maps to a concrete planning artifact in `.planning/phases/` where the full prompt context, execution details, and verification evidence live.

The project used a structured AI workflow: discuss → plan → execute → verify per phase. Every plan was executed by AI agents with human review gates; every claim was independently verified against the codebase.

---

## Entry 1: Toolchain & Tracer Setup

**Phase:** 01 | **Plan:** `.planning/phases/01-auditable-log-pipeline-analysis/01-01-PLAN.md`

**Task:** Lock the Python toolchain (CPython 3.12, uv, DuckDB 1.5.5, pytest, Ruff) and build an immutable one-line tracer from JSONL provenance through to Parquet output.

**AI contribution:** Generated `pyproject.toml` with pinned dependencies, Makefile skeleton, and the initial `pipeline/` package structure. Prompt: "Set up locked Python environment with DuckDB, pytest, Ruff; create pipeline package with CLI entry point."

**Assessment:** Straightforward scaffolding — AI produced correct `uv`-compatible project layout on first attempt. No hallucination risk at this stage.

**Verification:** `uv sync --locked` succeeds; `pytest -q` passes; `ruff check .` clean. Evidence: committed `uv.lock` (exact resolved versions).

---

## Entry 2: Provenance-First Ingestion & Validation

**Phase:** 01 | **Plan:** `.planning/phases/01-auditable-log-pipeline-analysis/01-02-PLAN.md`

**Task:** Build bounded JSONL ingestion with physical-line provenance and conservative validation rules.

**AI contribution:** Designed and implemented `pipeline/ingest.py` (source envelope with SHA-256, line number, byte-size guard), `pipeline/validate.py` (field-type checks, required-field presence, duplicate detection via canonical digest), and `pipeline/models.py` (typed dataclasses for Issue, Normalization, LedgerEntry, CleanRecord).

**Assessment:** The conservative disposition logic (any validation issue → REJECT unless explicitly repaired) required iterative refinement. Initial AI output conflated "issue detected" with "issue is fatal" — corrected by separating issue severity from final-action determination.

**Verification:** 2,923 input lines processed; 84 REJECT, 0 REPAIR, 2,839 ACCEPT. Strict UTF-8 decoding and JSON `parse_constant` hook reject non-standard values. Tests: `tests/pipeline/test_validation.py` (30+ assertions). Evidence: `data/evidence/phase1/quality_ledger.jsonl`.

---

## Entry 3: Normalization & Evidence Publication

**Phase:** 01 | **Plans:** `.planning/phases/01-auditable-log-pipeline-analysis/01-03-PLAN.md`

**Task:** Normalize timestamps (UTC conversion preserving raw offset), classify error types, write quality ledger, typed Parquet, and schema contract.

**AI contribution:** Implemented `pipeline/normalize.py` (ISO 8601 offset-aware parsing, UTC normalization, error-type taxonomy), `pipeline/write_outputs.py` (atomic JSONL/Parquet/JSON writes with `authorize_output_path`), and `pipeline/integrity.py` (SHA-256 inventory of immutable supplied files).

**Assessment:** Timestamp normalization correctly preserves the raw offset form alongside the UTC conversion — verified by checking round-trip fidelity. The error-type taxonomy uses explicit signature matching rather than regex guessing; 35 records classified as `UNCLASSIFIED_ERROR` (honest limit of the heuristic).

**Verification:** `data/processed/logs_clean.parquet` (2,839 rows, typed columns per `schema.json`). `data/evidence/phase1/source_manifest.json` hashes all supplied files. Tests confirm offset preservation and no silent coercion.

---

## Entry 4: SQL Analyses & Evidence Report

**Phase:** 01 | **Plans:** `.planning/phases/01-auditable-log-pipeline-analysis/01-04-PLAN.md` through `01-06-PLAN.md`

**Task:** Implement the four customer analyses as static SQL, generate CSV evidence tables, build the run manifest and reviewer report.

**AI contribution:** Generated `pipeline/sql/00_tracer_service_error_counts.sql` through `04_quality_reconciliation.sql` (DuckDB-dialect, parameter-bound), `pipeline/analysis.py` (registry pattern), `pipeline/manifest.py` (content-linked evidence graph with deterministic `run_id`), and `pipeline/report.py`.

**Assessment:** SQL was correct on first pass for the three straightforward queries. The "unusual day" heuristic (Q2) required explicit design discussion — AI initially proposed standard-deviation outlier detection; we chose a simpler "greater than 2× median" descriptive rule and documented it as a heuristic, not a statistical claim. This is an honest limitation.

**Verification:** All four tables in `data/evidence/phase1/tables/`. `run_manifest.json` `run_id` is content-derived (re-running yields identical hash). `make verify-phase1` passes end-to-end. The unusual-day heuristic identifies 2026-07-30 as the only qualifying date.

**Correction:** The `UNCLASSIFIED_ERROR` count (35/139 ERROR records) is documented in the report as a limitation — no fabricated classification was applied.

---

## Entry 5: Manifest Verification & Reconstruction

**Phase:** 01 | **Plans:** `.planning/phases/01-auditable-log-pipeline-analysis/01-07-PLAN.md`, `01-08-PLAN.md`

**Task:** Build verification that proves committed evidence is source-grounded (not just internally consistent).

**AI contribution:** Implemented `pipeline/manifest.py:verify_run_manifest` (re-reads inventory, re-checks hashes, re-counts rows, reconstructs `run_id`) and `pipeline/reconstruct.py` (byte-for-byte evidence reconstruction from canonical input to prove the ledger/Parquet were derived from the claimed source).

**Assessment:** The reconstruction approach is the strongest verification — a self-consistent forged evidence set could pass hash checks, but cannot pass reconstruction from immutable supplied bytes. AI correctly identified this gap when prompted about "what could a reviewer not trust about hash-only verification?"

**Verification:** `make verify-phase1` runs reconstruction; SHA-256 of reconstructed ledger matches committed ledger. 70 tests cover forgery, mismatch, and conservation scenarios.

---

## Entry 6: Version-Aware Knowledge Base

**Phase:** 02 | **Plan:** `.planning/phases/02-version-aware-knowledge-base-evaluation/02-01-PLAN.md`

**Task:** Build a local KB from 8 Vietnamese operational documents with version awareness and FTS5 search.

**AI contribution:** Implemented `kb/` package: `inventory.py` (document discovery, metadata extraction from Vietnamese header lines), `metadata.py` (regex parsing of version/date/department/approver), `versioning.py` (family grouping, `is_current` determination by effective date), `chunking.py` (heading-based splitting), `index.py` (SQLite FTS5 build with `bm25()` ranking), `search.py` (current-only and all-versions modes).

**Assessment:** Metadata extraction from Vietnamese documents required careful regex design — AI initially proposed overly rigid patterns that missed variant header formats. Iteratively corrected to handle "Ngày hiệu lực:", "Phiên bản:", etc. Version conflict resolution (POL-01 v1 vs v2) works correctly: v2 supersedes v1 based on effective date.

**Verification:** 8 documents → 22 chunks (20 current, 2 superseded). FTS5 queries return ranked results with source attribution. `data/evidence/phase2/chunks.jsonl` is the canonical export; `index.sqlite` is rebuildable.

---

## Entry 7: KB Evaluation & SOP

**Phase:** 02 | **Plan:** `.planning/phases/02-version-aware-knowledge-base-evaluation/02-02-PLAN.md`

**Task:** Evaluate retrieval quality with 10 predeclared cases and write a KB update SOP.

**AI contribution:** Designed 10 eval cases (`kb/eval_cases.py`) spanning 4 question types: direct_lookup (4), multi_source (3), version_trap (2), out_of_scope (1). Implemented `kb/eval_runner.py` (dual-dimension scoring: retrieval_hit + groundedness), `kb/eval_report.py` (JSON + Markdown output).

**Assessment:** Results: 9 pass, 1 partial (a multi-source case where one of two expected documents ranked outside top-5). Zero failures. The partial case is documented honestly — improving it would require semantic search or query expansion, which is beyond the FTS5 scope.

**Verification:** `data/evidence/phase2/eval_results.json` records all 10 cases with scores, queries, expected sources, and diagnoses. `sop/kb_update_sop.md` is one page, English.

---

## Entry 8: AWS Architecture Diagram & AI Response Review

**Phase:** 03 | **Plan:** `.planning/phases/03-aws-design-bedrock-extraction-evidence/03-01-PLAN.md`

**Task:** Design a conceptual AWS daily pipeline and review/correct 6 misleading AI claims from supplied material.

**AI contribution:** Generated `design/aws_daily_pipeline.drawio` (Draw.io XML with S3/Glue/Lambda/Athena/CloudWatch nodes, IAM boundaries, quarantine flow, uncertainty annotations). Wrote `design/aws_daily_pipeline.md` (669 words) and `design/ai_response_review.md` (640 words, 6 corrections with authoritative sources).

**Assessment:** The diagram is conceptual (not a deployable Terraform module) as required. AI correctly distinguished "POC local pipeline" from "production AWS architecture" in the explanation. The AI response review correctly identifies the Parquet misconception (row-based claim → actually columnar) and the Lambda timeout error (15 min stated as seconds).

**Verification:** Word counts within page limits (669/700 and 640/700). Each correction cites an authoritative source (AWS docs, supplied readings). `design/aws_daily_pipeline.png` is a rendered export (154 KB, 1542×762).

---

## Entry 9: Bedrock CLI & Extraction Prompt

**Phase:** 03 | **Plan:** `.planning/phases/03-aws-design-bedrock-extraction-evidence/03-02-PLAN.md`

**Task:** Build the Bedrock trial infrastructure: CLI scaffold, extraction prompt, test fixtures, evaluation method.

**AI contribution:** Implemented `design/bedrock.py` (Boto3 `Converse` wrapper with preflight validation), `design/cases.py` (5 test cases including ambiguous tc04 and edge-case tc05), `design/schema.py` (JSON schema + validation), `design/__main__.py` (argparse CLI: preflight/trial/report). Wrote `design/extraction_prompt.md` (451 words, strict JSON output contract).

**Assessment:** The prompt design uses explicit "no fabrication" rules and a fixed 5-field output schema. The evaluation method (`design/output/eval_method.md`) defines 3 measurable tiers without requiring a 3,000-inference live run — it is clearly labeled as a METHOD specification, not executed results.

**Verification:** 23 tests pass (mocked boto3). `design-report` is deterministic (no API calls, reads saved responses). Prompt word count: 451/1400 (within 2-page limit).

---

## Entry 10: Live Bedrock Trial & Model Selection

**Phase:** 03 | **Plan:** `.planning/phases/03-aws-design-bedrock-extraction-evidence/03-03-PLAN.md`

**Task:** Execute the 5-case Bedrock trial with a live model, record raw responses, assess results honestly.

**AI contribution:** Ran preflight → discovered Claude 3 Haiku is Legacy/unavailable in the configured account → dynamically selected `amazon.nova-lite-v1:0` via `list_foundation_models`. Executed all 5 cases at temperature 0.0.

**Assessment:** 3/5 pass (tc01–tc03). tc04 FAIL: model parsed "1/3" as a fraction instead of splitting the transaction descriptor. tc05 FAIL: model returned `confidence: "medium"` with `parse_status: "success"` (expected `partial`). These are genuine model limitations documented without repair.

**Correction:** Initial plan targeted `anthropic.claude-3-haiku-20240307-v1:0` — preflight rejected it as Legacy. The architecture handled this gracefully because model ID was always configurable (D-12). Switched to Nova Lite and re-ran. This is documented in `design/output/trial_observations.md` as an honest account-dependent finding.

**Verification:** `design/output/responses/tc01_raw.json` through `tc05_raw.json` committed (non-secret metadata only). `design/output/trial_summary.md` has field-level expected-vs-actual. `make design-report` regenerates summary deterministically without API calls.

---

## Entry 11: Submission Packaging & Audit

**Phase:** 04 | **Artifacts:** `.planning/phases/04-reviewer-ready-submission-handoff/04-CONTEXT.md`

**Task:** Assemble reviewer-facing navigation, consolidated evidence manifest, audit script, and this worklog.

**AI contribution:** Generated `scripts/make_manifest.py` (deterministic root `run_manifest.json` aggregating all phase evidence), `scripts/audit_submission.py` (automated submission checklist: deliverables, secrets, page limits, source integrity), expanded `README.md` with full navigation and limitations register.

**Assessment:** The manifest mirrors the Phase 1 pattern (content-derived `run_id`, SHA-256 hashes, no wall-clock fields). The audit script catches the absolute-path leak that was fixed during this phase.

**Verification:** `make manifest` produces deterministic output. `make audit-submission` passes all checks. `run_manifest.json` `run_id` is reproducible.

**Correction:** During Phase 4, discovered absolute machine paths (`/mnt/data/Minh/...`) leaked into committed evidence files (quality_ledger.jsonl, chunks.jsonl, eval_results.json). Fixed by making `source_path` repo-relative at the serialization boundary. Evidence was regenerated; all 201 tests pass after the fix.

---

## Limitations & Honest Findings

1. **UNCLASSIFIED_ERROR (35 records):** The error-type taxonomy uses explicit signature matching. Records that don't match known patterns are classified as `UNCLASSIFIED_ERROR` rather than force-fitted.

2. **Unusual-day heuristic:** The "greater than 2× median" rule is a descriptive heuristic, not a statistical test. It identifies one date (2026-07-30) but makes no inferential claim.

3. **Bedrock trial 3/5 pass rate:** Two failures are genuine model limitations (fraction parsing, confidence/status mismatch). No silent repair was applied.

4. **KB partial retrieval (1/10 cases):** One multi-source query returns only one of two expected documents in top-5. FTS5 lexical matching has inherent limits for semantic queries.

5. **Model availability:** Claude 3 Haiku was unavailable (Legacy status). Results are from Amazon Nova Lite — a different model may produce different extraction accuracy.

6. **Vietnamese content in KB fixtures:** Evaluation fixtures contain Vietnamese because the source operational documents are Vietnamese. This is source-derived, not a language-policy violation.
