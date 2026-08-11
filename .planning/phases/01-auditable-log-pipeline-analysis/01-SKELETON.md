# Walking Skeleton — Xbrain Data Engineer Assessment POC

**Phase:** 1
**Generated:** 2026-08-11

## Capability Proven End-to-End

> A reviewer can select one real immutable source line and trace it through source hashing, parsing, validation, UTC and error normalization, a ledger entry, DuckDB-written Parquet, a checked-in SQL result, and a manifest without changing the source file.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Application framework | CPython package with `argparse` stage subcommands | The assessed product is a local data workflow; a small CLI keeps every operation inspectable and avoids inventing a web surface. |
| Environment | `uv` project with committed `uv.lock` | A locked environment gives a clean-checkout reviewer one reproducible dependency resolution. |
| Data layer | Immutable JSONL input, JSONL quality ledger, DuckDB-written Parquet, static DuckDB SQL | This separates source provenance, row-level quality decisions, typed analytical storage, and executable answers. |
| Authentication | None | Phase 1 is an offline local CLI with no user, session, or network authentication boundary. |
| Deployment target | Documented local execution through Make and `uv run --locked` | AWS deployment is explicitly outside Phase 1; the local command is the full-stack execution target. |
| Directory layout | `pipeline/` source and SQL, `tests/pipeline/`, `data/processed/`, `data/evidence/phase1/` | The layout preserves the required submission area and keeps generated outputs outside `docs/onboard/datapack/`. |
| Integrity contract | SHA-256 inventory plus pre/post source checks and content-linked manifests | Every result must remain traceable to unchanged supplied bytes. |
| Output replacement | Deterministic ordering and atomic replacement inside an explicit generated-output root | Interrupted runs must not leave partially written artifacts, while the immutable input tree remains read-only. |

## Stack Touched in Phase 1

- [ ] Project scaffold — `pyproject.toml`, committed `uv.lock`, pytest, and Ruff.
- [ ] Routing — real `python -m pipeline` stage subcommands and Make targets.
- [ ] Data read/write — immutable JSONL read, JSONL ledger write, Parquet write, and DuckDB SQL read.
- [ ] Reviewer interaction — CLI arguments, exit codes, generated CSV/JSON/Markdown evidence, and one canonical command.
- [ ] Deployment — documented local `make phase1` execution; no cloud deployment is introduced.

## Out of Scope (Deferred to Later Slices)

- Phase 2 owns the version-aware SQLite FTS5 knowledge base, retrieval evaluation, and update SOP.
- Phase 3 owns the conceptual AWS design, supplied-AI-response review, extraction prompt, and five-case Bedrock trial.
- Phase 4 owns the repository-wide README and manifest audit, AI work log, limitations register, Git/submission audit, GitHub handoff, and ZIP backup.
- A browser UI, dashboard, conversational assistant, live AWS data-pipeline deployment, distributed processing, and full 3,000-line inference are outside the approved assessment scope.

## Subsequent Slice Plan

- Phase 1 expansion sequence: Plan 01 proves the tracer; Plan 02 completes validation/disposition; Plan 03 publishes ledger/Parquet evidence; Plans 04–05 produce the four static-SQL result tables; Plan 06 renders and verifies the report/manifest through the canonical command.
- Phase 2: A reviewer can search all supplied operational documents with deterministic current-version preference and inspect evaluation evidence.
- Phase 3: A reviewer can assess the bounded AWS proposal and five-case Bedrock evidence without secrets or unsupported claims.
- Phase 4: A reviewer can navigate, verify, audit, and receive the complete submission.
