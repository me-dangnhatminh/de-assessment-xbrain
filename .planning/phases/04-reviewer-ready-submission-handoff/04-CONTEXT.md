# Phase 4: Reviewer-Ready Submission & Handoff - Context

**Gathered:** 2026-08-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Assemble, audit, and document the complete assessment submission so a reviewer can navigate it, verify its reproducible evidence, and receive a repository that is ready for GitHub sharing and ZIP backup — with honest limits and no secrets or accidental local state. This phase produces reviewer-facing navigation and audit artifacts; it does not add new pipeline, KB, or Bedrock capabilities.

</domain>

<decisions>
## Implementation Decisions

### AI Worklog (AILOG-01..03, DOC-01)
- **D-01:** Use `.planning/` as the primary source of truth for the AI worklog. The `.planning/phases/` directories already record every plan, decision (CONTEXT.md), discussion log, and execution summary, which constitutes a genuine, chronologically plausible record of AI-assisted work. `AI_WORKLOG.md` will be a concise digest/summary at the top level that points into `.planning/` rather than re-listing 8–15 standalone entries with full prompts. — **Reversibility:** reversible — AI_WORKLOG.md is a single document that can be expanded later without touching other deliverables.
- **D-02:** The digest must still satisfy the AILOG requirements reviewer-facing: each referenced phase maps to its task, prompt source, AI output location, critical assessment, and independent verification/correction (e.g. the Bedrock trial 3/5 pass and its corrections). Honest limitations and at least one genuine correction must be visible.

### Consolidated Evidence Manifest (RPRO-03)
- **D-03:** Generate a root-level `run_manifest.json` (top level of the repository, next to `README.md`) that consolidates evidence across all phases: input hashes, configuration, commands, output paths, row counts, and non-secret runtime metadata. It is produced deterministically by a generator command (e.g. `make manifest` or a `scripts/` entry point) that aggregates the Phase 1 pipeline manifest, Phase 2 KB artifacts, and Phase 3 Bedrock preflight/trial metadata. — **Reversibility:** reversible — a new generated file; existing per-phase manifests remain untouched.

### Limitations Register (DOC-04)
- **D-04:** The limitations register lives as a **README section** ("Limitations, Assumptions & Deferred Work") inside the root `README.md`, not as a separate file. It separates: verified results, design assumptions, account-dependent behavior (Bedrock region/model access), and deliberately deferred work. — **Reversibility:** reversible — moving a doc section between files is cheap.

### Secrets Hygiene & Packaging (DOC-05, DOC-06)
- **D-05:** Add an audit script + documented checklist (make target, e.g. `make audit-submission`) that verifies: no committed secret material, `.env` is git-ignored, required top-level deliverables exist, page limits are respected, tests and lint pass, source integrity is preserved (`docs/onboard/` unchanged), and a ZIP exclude list is provided for backup. — **Reversibility:** reversible — additive tooling; no existing artifact changes.
- **D-06:** Repository must be ready for GitHub sharing and ZIP backup without generated secrets or accidental local state (e.g. `.venv`, `.pytest_cache`, `.ruff_cache`, `.env` excluded).

### the agent's Discretion
- Exact structure/heading style of `AI_WORKLOG.md` digest.
- Command names and Makefile target names for the audit and manifest generation.
- Where the README section ordering places the limitations register.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Assessment & Requirements
- `.planning/REQUIREMENTS.md` — RPRO-03, RPRO-04, AILOG-01..03, DOC-01..06 define Phase 4 acceptance criteria.
- `.planning/ROADMAP.md` §Phase 4 — Goal, mode, dependencies, success criteria.
- `.planning/PROJECT.md` — Project core value (reproducible, source-grounded, defensible evidence) and constraints (English, page limits, preserved source files, version control).

### Existing Phase Artifacts (sources for the worklog digest and consolidated manifest)
- `.planning/phases/01-auditable-log-pipeline-analysis/` — CONTEXT, DISCUSSION-LOG, PLAN/SUMMARY files; pipeline evidence in `data/evidence/phase1/run_manifest.json`.
- `.planning/phases/02-version-aware-knowledge-base-evaluation/` — CONTEXT, PLAN/SUMMARY; KB artifacts in `kb/` (chunks.jsonl, index.sqlite, evaluation results).
- `.planning/phases/03-aws-design-bedrock-extraction-evidence/` — CONTEXT, PLAN/SUMMARY; Bedrock trial evidence in `design/output/` (preflight_result.json, responses/tc01..05_raw.json, trial_summary.md).
- `docs/onboard/` — immutable supplied assessment material; `01_Domain_POC.md`, `02_AI_Proficiency.md`.

### Reviewer-Facing Deliverables
- `README.md` — root reviewer navigation; must be expanded to cover all phases, outputs, limitations, and commands.
- `Makefile` — existing verification targets (`make verify`, `make phase1`, etc.); new targets for manifest/audit.
- `pipeline/manifest.py` — existing Phase 1 manifest logic to model the consolidated generator on.
- `.gitignore` — must cover `.env`, `.venv`, caches; `.env.example` documents non-secret settings.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline/manifest.py`: Phase 1 run-manifest generation logic — reuse its deterministic hashing/metadata patterns for the consolidated root manifest.
- `Makefile`: existing `verify`/`verify-phase1` targets — extend the pattern for `manifest`, `audit-submission`.
- `.env.example`: template for non-secret Bedrock configuration documentation.
- `scripts/`: existing entry points — a natural home for the consolidated manifest generator and audit script.

### Established Patterns
- Generated evidence lives in project output locations; supplied files under `docs/onboard/` are never modified (verified via git diff checks in `make verify-phase1`).
- Deterministic outputs preferred (content-derived IDs, no wall-clock fields where avoidable); row counts and hashes recorded as auditable claims.
- English throughout reviewer-facing material; page limits (one page / two pages) respected where specified.

### Integration Points
- Root `README.md` becomes the single reviewer entry point linking `pipeline/`, `kb/`, `design/`, `sop/`, `AI_WORKLOG.md`.
- `AI_WORKLOG.md` links into `.planning/phases/*/` artifacts.
- Consolidated `run_manifest.json` aggregates per-phase evidence paths that already exist on disk.

</code_context>

<specifics>
## Specific Ideas

- User explicitly asked whether `.planning/` could substitute for a full standalone AI worklog because it "records every plan and choice" — the digest approach (D-01/D-02) is the agreed answer.
- User prefers generated, reproducible artifacts over hand-written manifest tables (chose "Root run_manifest.json, generated").
- User prefers the limitations register inside the README rather than a separate file.
- User chose an audit script + checklist for hygiene rather than manual-only verification.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-Reviewer-Ready Submission & Handoff*
*Context gathered: 2026-08-12*
