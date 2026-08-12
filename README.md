# Xbrain Data Engineer Assessment POC

A submission-grade local proof of concept for the Xbrain Data Engineer (AI / Knowledge Engineering) assessment. Delivers a Python data pipeline, operational knowledge base, AWS design artifacts, and Bedrock extraction evidence for the fictional Sao Do Finance customer.

**Core value:** Every claimed result is reproducible, source-grounded, and defensible in a technical interview.

---

## Deliverable Map

| Area | Path | Description |
|------|------|-------------|
| Data pipeline | `pipeline/` | JSONL → quality ledger → typed Parquet → SQL analyses |
| Knowledge base | `kb/` | Version-aware FTS5 index over 8 Vietnamese operational docs |
| AWS design | `design/` | Conceptual daily pipeline diagram + AI response review |
| Bedrock trial | `design/output/` | 5-case structured extraction with raw responses |
| SOP | `sop/` | One-page KB update procedure |
| AI worklog | `AI_WORKLOG.md` | 11-entry digest of AI-assisted work with corrections |
| Evidence | `data/evidence/` | Phase 1 manifest, ledger, tables; Phase 2 eval results |
| Manifest | `run_manifest.json` | Consolidated cross-phase evidence (deterministic) |

---

## Quick Start

Prerequisites: CPython 3.12–3.14, [uv](https://docs.astral.sh/uv/), GNU Make, Git.

```bash
uv sync --locked          # exact locked environment
make phase1               # pipeline: ingest → validate → analyze → report → verify
make phase2               # KB: build index → evaluate retrieval
make design-report        # Bedrock: deterministic report from saved responses (FREE, no API)
make manifest             # generate consolidated run_manifest.json
make audit-submission     # verify submission readiness
```

**Full verification** (regenerates all deterministic evidence + tests + lint + audit):

```bash
make verify
```

> **Note:** `make phase3` and `make design-trial` invoke paid Bedrock API calls. Use `make design-report` for free deterministic re-reporting from saved responses.

---

## Phase 1: Auditable Log Pipeline

Turns the supplied seven-day Sao Do Finance log (2,923 lines) into:
- A source-preserving quality ledger (`data/evidence/phase1/quality_ledger.jsonl`)
- A typed Parquet dataset (`data/processed/logs_clean.parquet`, 2,839 rows)
- Four reproducible SQL analyses (`data/evidence/phase1/tables/`)
- A content-linked evidence manifest (`data/evidence/phase1/run_manifest.json`)

```bash
make phase1           # canonical workflow
make verify-phase1    # + lock check, lint, tests, source integrity
```

**Independently runnable stages:**

```bash
uv run --locked python -m pipeline integrity   # SHA-256 inventory of supplied files
uv run --locked python -m pipeline validate    # validation-only pass (no output)
uv run --locked python -m pipeline run         # full evidence generation
uv run --locked python -m pipeline analyze     # SQL analyses only
uv run --locked python -m pipeline report      # manifest + report only
uv run --locked python -m pipeline verify      # reconstruction verification
```

All stages accept `--input`, `--output-root`, and `--max-line-bytes`.

**Key findings:** payment-api has the highest ERROR count (139). 2026-07-30 is the only date exceeding the 2×-median heuristic. 35 records are classified as `UNCLASSIFIED_ERROR` (honest limit of signature matching).

---

## Phase 2: Version-Aware Knowledge Base

Builds a local SQLite FTS5 knowledge base from 8 Vietnamese operational documents with version-aware metadata resolution.

```bash
make phase2           # build + evaluate
uv run --locked python -m kb search --db data/evidence/phase2/index.sqlite --query "sao lưu" --mode current
```

**Evaluation:** 10 predeclared cases (4 direct_lookup, 3 multi_source, 2 version_trap, 1 out_of_scope). Results: 9 pass, 1 partial, 0 fail. Evidence: `data/evidence/phase2/eval_results.json`.

**SOP:** `sop/kb_update_sop.md` — one-page English procedure for adding/updating documents.

---

## Phase 3: AWS Design & Bedrock Extraction

### AWS Daily Pipeline Design

- **Diagram:** `design/aws_daily_pipeline.png` (source: `.drawio`)
- **Explanation:** `design/aws_daily_pipeline.md` (≤1 page, 669 words)
- Covers: S3 → Glue → Lambda → Athena flow, IAM boundaries, failure handling, POC-vs-production distinction, 4 documented uncertainties

### AI Response Review

- `design/ai_response_review.md` (≤1 page, 640 words)
- Corrects 6 misleading claims with authoritative sources

### Structured Extraction Prompt & Trial

- **Prompt:** `design/extraction_prompt.md` (≤2 pages, 451 words)
- **Evaluation method:** `design/output/eval_method.md` (3-tier measurable framework)
- **Trial:** 5 cases against `amazon.nova-lite-v1:0` (ap-northeast-1)
- **Result:** 3/5 pass. tc04/tc05 fail on fraction parsing and confidence mismatch.
- **Raw responses:** `design/output/responses/tc01_raw.json` through `tc05_raw.json`

```bash
make design-report    # deterministic re-report (no API calls, no cost)
```

---

## Evidence & Manifest

The root `run_manifest.json` consolidates evidence across all phases:

```bash
make manifest         # regenerate (deterministic, content-derived run_id)
```

Per-phase evidence locations:
- Phase 1: `data/evidence/phase1/` (manifest, ledger, schema, tables, report)
- Phase 2: `data/evidence/phase2/` (chunks.jsonl, index.sqlite, eval_results.json, eval_report.md)
- Phase 3: `design/output/` (preflight_result.json, responses/, trial_summary.md, observations)

---

## Submission Audit

```bash
make audit-submission
```

Checks: required deliverables exist, page limits respected, source integrity preserved, no secrets or machine paths in committed files, .gitignore covers caches, tests pass, lint clean.

---

## Limitations, Assumptions & Deferred Work

### Verified Results with Known Limits

| Finding | Limit | Documented in |
|---------|-------|---------------|
| Error-type taxonomy | 35/139 ERROR records → `UNCLASSIFIED_ERROR` (no forced classification) | `data/evidence/phase1/report.md` |
| Unusual-day heuristic | Descriptive 2×-median rule, not a statistical test | `data/evidence/phase1/report.md` |
| KB retrieval | 1/10 cases partial (multi-source FTS5 limit) | `data/evidence/phase2/eval_results.json` |
| Bedrock trial | 3/5 pass; 2 failures are model limitations (not prompt bugs) | `design/output/trial_summary.md` |

### Design Assumptions

- **Local execution only:** AWS deployment is out of scope; `design/` is conceptual.
- **SQLite FTS5 for KB:** 8 documents do not justify an embedding service or vector database.
- **Conservative dispositions:** Any unresolvable validation issue → REJECT (no silent coercion).
- **Deterministic outputs:** Content-derived IDs, no wall-clock fields, reproducible on any machine.

### Account-Dependent Behavior

- **Model availability:** Claude 3 Haiku was Legacy/unavailable; trial used Amazon Nova Lite. A different account/region may have different models available.
- **Region:** `ap-northeast-1`. Model behavior may vary by region.
- **Bedrock access:** Requires enabled model access in the AWS account. Preflight validates this.

### Deliberately Deferred

- Docker-based clean-room verification (available via `make clean-checkout-verify` but not part of the main workflow)
- Semantic/vector search for KB (FTS5 is sufficient for 8 documents)
- Production error alerting or monitoring
- Multi-language support for reviewer-facing material (English throughout as required)

---

## Integrity & Source Preservation

`docs/onboard/` contains immutable supplied assessment material. The pipeline verifies a sorted SHA-256 inventory before and after production runs. `git diff --exit-code -- docs/onboard` is part of every verification target.

All generated evidence lives in `data/`, `design/output/`, and root-level files. Supplied files are never modified.

---

## Language & Page Limits

- All reviewer-facing material (README, design docs, SOP, worklog, comments, report prose) is in English.
- KB source documents and evaluation fixtures contain Vietnamese because the supplied operational documents are Vietnamese — this is source-derived content, not a policy violation.
- Page limits: AWS explanation ≤1 page (669/700 words), AI response review ≤1 page (640/700 words), extraction prompt ≤2 pages (451/1400 words).

---

## Repository Hygiene

- `.env` is git-ignored; `.env.example` documents non-secret configuration variables.
- `.pytest_cache/`, `.ruff_cache/`, `.venv/`, `__pycache__/` are all git-ignored.
- No AWS credentials, account IDs, or machine-specific paths in committed files.
- ZIP packaging: `git archive --format=zip --prefix=xbrain-assessment/ HEAD -o xbrain-assessment.zip`
