# Phase 4 Research: Reviewer-Ready Submission & Handoff

**Gathered:** 2026-08-12
**Status:** Ready for planning

> Research findings grounded in the existing codebase. This is the technical baseline the
> planner uses to author executable PLAN.md tasks for Phase 4.

## 1. Inventory of Existing Evidence Artifacts + Real Paths

All paths exist on disk and are committed (unless noted).

**Phase 1 — Log pipeline (under `data/`):**
- `data/evidence/phase1/run_manifest.json` — Phase 1 evidence graph (schema in §2)
- `data/evidence/phase1/source_manifest.json` — sorted SHA-256 inventory of all `docs/onboard/` files
- `data/evidence/phase1/quality_ledger.jsonl` — 2,923 lines, one per physical input line, with `final_action`, `issues`, `normalizations`, `raw_line`, `record_digest`, `source_path`
- `data/evidence/phase1/schema.json`, `data/evidence/phase1/report.md`
- `data/evidence/phase1/tables/01_service_error_counts.csv` … `04_quality_reconciliation.csv`
- `data/processed/logs_clean.parquet` (2,839 rows)
- `pipeline/sql/00_tracer_service_error_counts.sql` … `04_quality_reconciliation.sql`
- Source modules: `pipeline/{manifest,integrity,ingest,validate,normalize,analysis,report,reconstruct,write_outputs,models,__main__}.py`

**Phase 2 — KB (under `data/evidence/phase2/` and `kb/`):**
- `data/evidence/phase2/chunks.jsonl` — 22 chunk records, canonical export
- `data/evidence/phase2/index.sqlite` — rebuildable FTS5 index
- `data/evidence/phase2/eval_results.json` — 10 cases, `retrieval_hit_totals` (9/1/0), per-case `question_type`, `query_used`, `search_mode`, `retrieval_hit_score`, `groundedness_score`, `diagnosis`, `expected_sources`
- `data/evidence/phase2/eval_report.md`
- `kb/` source modules: chunking, index, inventory, metadata, versioning, search, eval_cases, eval_runner, eval_report, models, `__main__`
- `sop/kb_update_sop.md` — one-page English SOP (SOP-01/SOP-02)

**Phase 3 — AWS design + Bedrock trial (under `design/`):**
- `design/aws_daily_pipeline.drawio`, `.png`, `.md` (46-line English explanation, ≤1 page)
- `design/ai_response_review.md` (53 lines, ≤1 page)
- `design/extraction_prompt.md` (81 lines, ≤2 pages)
- `design/output/preflight_result.json` — `{status: "pass", model_id: "amazon.nova-lite-v1:0", region: "ap-northeast-1", boto3_version, timestamp_utc}`
- `design/output/responses/tc01_raw.json` … `tc05_raw.json` — committed (via `git add -f`)
- `design/output/trial_summary.md` (3/5 pass), `trial_observations.md`, `eval_method.md` (3,000-line plan)
- Source modules: `design/bedrock.py`, `design/cases.py`, `design/schema.py`, `design/__main__.py`

**Missing today (DOC-01):** `AI_WORKLOG.md` does not exist; root `README.md` is Phase-1-only.

**Critical finding (DOC-06, accidental local state):** Absolute machine paths leak into committed
generated evidence — `source_path` in `quality_ledger.jsonl` (2,923), `chunks.jsonl` (22),
`eval_results.json` (in `index_path`), and `eval_report.md`. The audit/manifest must address this
(normalize to repo-relative or document an explicit exception).

## 2. Manifest Pattern from `pipeline/manifest.py`

`pipeline/manifest.py` is the model to mirror for the consolidated generator:
- **Deterministic payload** built from existing generated evidence, no recomputation. Keys:
  `run_id`, `source_manifest_sha256`, `source_inventory`, `runtime` (duckdb/python/uv versions,
  no wall-clock), `commands`, `row_counts` (sorted), `artifacts` (sorted by path), `analyses`.
- **Hashing:** `sha256_file()` per artifact; content-derived SHA-256 for descriptors.
- **`run_id`:** content hash of the sorted JSON payload — re-running yields identical `run_id`.
- **Row counts:** `_line_count` (JSONL), `_csv_row_count`, `_parquet_row_count` (DuckDB COUNT),
  `_ledger_action_counts` (strict line-by-line parse).
- **Atomic publish:** `write_json_atomic(authorize_output_path(...), manifest)`; `validate_output_root`
  refuses repo root and `docs/onboard`.
- **Verification:** `verify_run_manifest` fails closed (re-reads inventory, re-checks hashes/row
  counts, reconstructs evidence, recomputes `run_id`).
- Reusable: `sha256_file`/`inventory_supplied_inputs` in `pipeline/integrity.py`;
  `write_json_atomic`/`write_parquet_atomic` in `pipeline/write_outputs.py`.

## 3. Makefile Targets Inventory

- Canonical form: `uv run --locked python -m ...`.
- Existing: `sync`, `integrity`, `pipeline`, `analysis`, `report`, `phase1`, `verify-phase1`
  (phase1 + `uv lock --check` + `ruff check .` + `ruff format --check --exclude .planning .` +
  `pytest -q` + `git diff --exit-code -- docs/onboard`), `clean-checkout-verify`; Phase 2:
  `kb-build`, `kb-search`, `kb-eval`, `phase2`; Phase 3: `design-preflight`, `design-trial`
  (PAID), `design-report` (deterministic, no API), `phase3` (preflight+trial+report).
- **`.PHONY` gap:** `design-*` and `phase3` are missing from `.PHONY`.
- Phase 4 gaps: no `verify` umbrella, no `manifest`, no `audit-submission`, no ZIP target.
- **Important:** `make phase3` triggers paid trial calls — the clean-output smoke check and audit
  must NOT re-run the trial; use `design-report` (deterministic) and treat saved raw responses as
  immutable evidence.

## 4. README Current Structure + Gaps

Current (all Phase 1):
1. Title + one-sentence description
2. "Phase 1 quick start" (`uv sync --locked`, `make phase1`, `make verify-phase1`, Docker)
3. "Independently runnable stages" (6 CLI commands)
4. "Evidence map and findings"
5. "Integrity, assumptions, and boundaries"

Gaps:
- No navigation table to required deliverables: `pipeline/`, `kb/`, `design/`, `sop/`,
  `AI_WORKLOG.md` (DOC-01)
- No Phase 2/3 quick starts or commands (`make phase2`, `design-report`, KB search/eval)
- No "Limitations, Assumptions & Deferred Work" register section (DOC-04)
- No consolidated `run_manifest.json` section/link, no secrets-hygiene instructions, no ZIP-backup
  instructions, no submission audit checklist
- No statement of page limits / English policy
- Last line references Phase 2/3 deliverables as "future work" — must be updated
- README is English today (passes DOC-03)

**English audit nuance (DOC-03):** KB evaluation fixtures and generated reports contain Vietnamese
because the supplied operational docs are Vietnamese. The audit must scope "English throughout
reviewer-facing material" to navigation/docs/comments/report prose and justify fixture content as
source-derived. A blunt "no non-ASCII" check would false-fail the KB evidence set.

## 5. Secrets / `.gitignore` / `.env` Hygiene Baseline

- `.gitignore`: `.tmp`, `.venv/`, `__pycache__/`, `*.py[cod]`, `design/output/responses/`, `.env`
- `.env` is git-ignored, non-secret config only (`AWS_REGION`, `BEDROCK_MODEL_ID`,
  `BEDROCK_MAX_TOKENS`, `BEDROCK_TEMPERATURE`). `.env.example` tracked and documents vars + `AWS_PROFILE`.
- **Gaps:** `.pytest_cache/` and `.ruff_cache/` NOT gitignored (merely untracked) — must be excluded
  from ZIP. `.tmp/` ignored but present on disk.
- Raw Bedrock responses committed despite ignore rule — audit must verify no credentials/account IDs.
- Abs path leak (§1) is the real portability risk.
- One untracked file: `.planning/phases/03-.../03-VERIFICATION.md` — must be committed.

## 6. Tests + Lint Commands

- `pyproject.toml`: `testpaths=["tests"]`, `pythonpath=["."]`; ruff `target-version="py312"`,
  `line-length=100`. Dev deps: `pytest==9.1.1`, `ruff==0.16.2`.
- Tests: `tests/pipeline/` (6 files), `tests/kb/` (8), `tests/design/` (3) — **195 `def test_`**
  functions. Runs with plain `pytest -q`.
- Lint: `ruff check .` and `ruff format --check --exclude .planning .`.
- Reuse gates in `audit-submission`: `uv lock --check`, the two ruff commands, `pytest -q`,
  `git diff --exit-code -- docs/onboard`.

## 7. AI Worklog Source Material

- `.planning/phases/` holds 4 phase dirs (47 files). Phase 1: 8 PLAN+SUMMARY pairs + CONTEXT,
  DISCUSSION-LOG, PATTERNS, RESEARCH, REVIEW, SECURITY, SKELETON, SOURCE-AUDIT, UAT, VERIFICATION.
  Phase 2: 2 PLAN/SUMMARY + CONTEXT, DISCUSSION-LOG, REVIEW, VERIFICATION. Phase 3: 3 PLAN/SUMMARY +
  CONTEXT, DISCUSSION-LOG, RESEARCH, REVIEW, VERIFICATION (untracked). Phase 4: CONTEXT + DISCUSSION-LOG.
- **Git history: 112 commits**, conventionally formatted per phase — genuine incremental record
  satisfying DOC-06, supplies chronology for AILOG-01.
- **Genuine correction material (AILOG-03):** Bedrock trial switched from
  `anthropic.claude-3-haiku-20240307-v1:0` (Legacy/Rejected) to `amazon.nova-lite-v1:0`;
  3/5 pass with tc04/tc05 FAIL — in `trial_observations.md`/`trial_summary.md`. Also the `fix(01)`
  commit series (strict UTF-8/JSON parsing, reconstruction verification).
- **13 sub-plans** (8+2+3) naturally yield 8–15 digest entries.

## 8. Recommended Implementation Approach (grounded in what exists)

**Consolidated manifest (`run_manifest.json`, root, D-03):**
- Add `scripts/` entry point (e.g. `scripts/make_manifest.py` or a `submission/` module) wired as
  `make manifest`. Do NOT put in `pipeline/` (Phase-1 scoped).
- Mirror `pipeline/manifest.py`: build payload from existing per-phase manifests/artifacts (no
  recomputation), reuse `sha256_file`/`inventory_supplied_inputs`; include `run_id` (content hash),
  Phase 1 pointer + row counts, Phase 2 chunks/eval summary, Phase 3 preflight metadata + trial pass
  rate + raw response hashes, `commands`, `runtime`, `artifacts` list. Deterministic ordering; write
  atomically.
- Reference `design-report`, don't re-run the trial.

**Audit (`make audit-submission`, D-05):**
- New `scripts/audit_submission.py` + documented checklist. Checks:
  - Required deliverables exist: `pipeline/`, `kb/`, `design/`, `sop/`, `AI_WORKLOG.md`, `README.md`,
    root `run_manifest.json`
  - Tests/lint: `pytest -q`, `ruff check .`, `ruff format --check --exclude .planning .`
  - Source integrity: `git diff --exit-code -- docs/onboard` + compare `source_manifest.json` hashes
    against live inventory
  - Secrets hygiene: no tracked `.env`; scan for credential patterns + the abs path `/mnt/data/Minh`;
    verify `.pytest_cache/`, `.ruff_cache/`, `.venv/`, `.env`, `.tmp`, `__pycache__` untracked
  - Page limits: line-count checks for the four bounded docs
  - English scoped to reviewer-facing prose (not KB fixtures); `.planning` excluded from format/English
  - Clean-output smoke: `make phase1` + `kb-build`/`kb-eval` + `design-report`, then re-verify
  - Git state clean; ZIP exclude list (`git archive --format=zip --prefix=xbrain-assessment/`)

**Remediation items before audit can pass:**
(a) normalize absolute `source_path`/`index_path` to repo-relative (or document exception),
(b) add `.pytest_cache/`/`.ruff_cache/` to `.gitignore`, (c) commit `03-VERIFICATION.md`,
(d) add `design-*`/`phase3` to `.PHONY`.

**README updates (DOC-01/02/04):**
- Navigation section to deliverables; Phase 2/3 quick starts (note `design-trial` paid,
  `design-report` free); "Limitations, Assumptions & Deferred Work" register; "Submission Audit &
  Packaging" section; page-limit/English policy statement.

**AI worklog digest (`AI_WORKLOG.md`, D-01/D-02):**
- Top-level digest linking into `.planning/phases/*/`; 13 natural entries (8+2+3), chronologically
  plausible (matches 112-commit history). Each maps task → prompt source → AI output → assessment →
  verification → corrections. Surface honest limitations (AILOG-03): legacy-model rejection, 2/5
  trial failures, KB partial case, `UNCLASSIFIED_ERROR` count, descriptive-only anomaly rule.
