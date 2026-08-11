<!-- GSD:project-start source:PROJECT.md -->

## Project

**Xbrain Data Engineer Assessment POC**

This repository is a submission-grade proof of concept for the August 2026 Xbrain Data Engineer (AI / Knowledge Engineering) assessment. It delivers a local Python data pipeline and operational knowledge base for the fictional Sao Do Finance customer, together with the required AI-proficiency artifacts and reproducible evidence that every result was verified.

The finished repository is intended for Xbrain and TechX evaluators. It must demonstrate sound judgment, an honest and traceable working process, and the ability to explain every submitted line—not merely produce plausible-looking outputs.

**Core Value:** Every claimed result must be reproducible, source-grounded, and understandable enough for the candidate to defend in a technical interview.

### Constraints

- **Timeline**: Two days — prioritize a complete, runnable, well-evidenced submission over unnecessary architectural complexity.
- **Implementation**: Python and local execution for the data pipeline — AWS deployment is not required.
- **Cloud AI**: Amazon Bedrock — AWS credentials, region access, and an enabled model are available for the five-case live prompt trial.
- **Language**: English throughout — README, supporting documents, code comments, reports, and evaluation artifacts.
- **Length**: AWS explanation and AI-response review are each no more than one page; the structured-extraction prompt task is no more than two pages.
- **Data integrity**: Supplied source files must remain unchanged — generated datasets, indexes, and reports live in project output locations.
- **Evidence**: All reported results must be regenerable through documented commands and backed by tests, queries, evaluation records, or authoritative sources.
- **Submission shape**: Preserve the required top-level deliverable areas: `pipeline/`, `kb/`, `design/`, `sop/`, `AI_WORKLOG.md`, and the root `README.md`.
- **Version control**: Commit along the real implementation progression rather than squashing all work into a final commit.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommendation in One Sentence

## Recommended Stack

### Core Framework

| Technology | Version guidance | Purpose | Why |
|---|---:|---|---|
| CPython | `>=3.12,<3.15`; prefer the 3.13 patch release available on the submission machine | One local runtime | Python is required by the brief. The constraint includes the workspace's verified Python 3.12.3 while preferring the mature 3.13 line; it excludes an untested future major/minor. Record `python --version` in the run evidence. |
| `uv` | Current stable; commit the generated `uv.lock` | Environment and dependency resolution | `uv.lock` records exact resolved cross-platform packages and `uv sync --locked` verifies a reviewer gets the same environment. Do not hand-edit the lock file. |
| Python standard library | CPython bundled | CLI, JSONL parsing, validation, hashing, SQLite access, report JSON | `argparse`, `json`, `datetime`, `pathlib`, `hashlib`, `sqlite3`, and `logging` make the pipeline explicit. Prefer small named validation functions returning a record plus issue codes over a framework that obscures cleaning decisions. |

### Data, Query, and Storage

| Technology | Version guidance | Purpose | Why |
|---|---:|---|---|
| DuckDB Python client | `duckdb==1.5.5` at research time; keep exact resolved version in `uv.lock` | Transform valid records, write Parquet, execute the four SQL analyses | It reads JSON and Parquet directly and reads/writes Parquet efficiently. One embedded dependency replaces a pandas + database-server combination and keeps the submitted SQL executable. |
| Apache Parquet | Written by DuckDB | Canonical cleaned-log dataset | A columnar, typed output is appropriate for the required aggregation questions. Preserve raw JSONL unchanged; write `data/processed/logs_clean.parquet` only after validation. |
| JSONL/JSON audit artefacts | Standard library | Rejected/repair decisions and summaries | Write a row-level reject/repair ledger with source line number, issue code, original value, action, and reason. It is more reviewable than burying data-quality evidence in logs. |
| SQLite FTS5 | CPython `sqlite3`; preflight that FTS5 is compiled in | Local KB catalogue, chunks, metadata, lexical search | FTS5 supports ranked full-text search with `bm25()`. Eight structured operational documents do not justify an embedding service or vector database. Store each chunk's source, section, version, effective date, owner, status, and content hash in normal SQLite columns; use FTS only to search content. |

### AI, Testing, and Documentation

| Technology | Version guidance | Purpose | Why |
|---|---:|---|---|
| Boto3 | `boto3==1.43.68` at research time; lock exact version | The required five Amazon Bedrock prompt trials | Use direct `bedrock-runtime` `Converse` calls, not LangChain or an agent framework. The API is model-agnostic for models that support it and yields a small, auditable request/response surface. |
| Amazon Bedrock control plane | AWS service; no package beyond Boto3 | Account/Region preflight | Call `bedrock.list_foundation_models()` and/or `get_foundation_model()` before the trial. Select a text model that is **ACTIVE**, available in the selected Region, supports `Converse`, and is permitted for the account. Pass its ID through `BEDROCK_MODEL_ID`; do not commit or promise a hard-coded model ID. |
| `pytest` | `pytest==9.1.1` at research time; lock exact version | Deterministic unit and end-to-end checks | Test each validation rule, repair rule, no-mutation guarantee, SQL output shape, metadata freshness rule, retrieval hit, and out-of-scope refusal. This is the smallest credible test framework for a Python submission. |
| Ruff | `ruff==0.16.2` at research time; dev dependency | Fast formatting/lint evidence | One dev tool catches simple quality mistakes without a formatter/linter stack. Use `ruff check .` and `ruff format --check .` in the documented verification command. |
| Markdown, `Makefile`, Git, SHA-256 manifest | No runtime dependency | Reproducible documentation and evidence | The root README names every command. A `make verify` target should run locked sync, tests, lint, pipeline, KB rebuild, and checks; a generated manifest hashes immutable inputs and generated evidence. |

## Required Dependencies

## Concrete Boundaries and Artefacts

| Boundary | Recommended implementation | Submitted/rebuilt evidence |
|---|---|---|
| Raw ingestion | Stream JSONL one line at a time; retain source line number and never write to `docs/onboard/datapack/`. | Input SHA-256 manifest; validation ledger. |
| Validation/cleaning | Explicit `validate_record()` and narrowly named repairs; reject malformed JSON or unrepairable records, never silently coerce. | Issue counts by code, repair/reject ledger, tests. |
| Analytics | DuckDB loads the cleaned Parquet dataset; checked-in `.sql` contains all four customer questions. | Re-runnable SQL and result tables/CSV or Markdown. |
| KB build | Markdown headings become chunks; normalize document metadata into SQLite, calculate `is_current` deterministically per document family/effective date, then insert current and historical chunks into FTS5. | `kb/chunks.jsonl` (human-readable canonical chunk export), rebuildable `kb/index.sqlite`, and evaluation results. |
| Retrieval | Query FTS5 with parameter binding and `ORDER BY bm25`; filter/re-rank to current effective documents for normal answers, while retaining historical chunks for provenance/evaluation. | Top-k results containing source/section/version/effective date and retrieval-hit tests. |
| Bedrock trial | A tiny script reads five fixed cases and makes one `Converse` request each with deterministic low-temperature settings where the selected model supports them. Persist request metadata and raw response separately from secrets. | `model_id`, Region, SDK version, prompt SHA-256, timestamps, raw response JSON, parsed comparison, and pass/fail observations. |

## Avoidable Complexity

| Category | Recommended | Alternative rejected | Why not for this two-day POC |
|---|---|---|---|
| Data manipulation | DuckDB SQL | pandas + SQLAlchemy + local PostgreSQL | Multiple overlapping data layers add installation risk and make it harder to explain which engine produced the reported result. |
| Validation | Explicit standard-library functions and issue codes | Pydantic / Great Expectations | Pydantic v2 is valid if a future strict API boundary needs it, but the fixed log schema needs transparent per-field rules; Great Expectations is far beyond the evidence required. |
| KB search | SQLite FTS5 lexical search | Chroma, FAISS, managed vector store, Amazon Bedrock Knowledge Bases | The brief accepts SQLite FTS; version-aware metadata and evaluation matter more than semantic retrieval at eight documents. Extra services would obscure the version-conflict logic. |
| LLM integration | Boto3 `Converse` adapter | LangChain/LlamaIndex/agent framework | The deliverable is five structured-extraction tests, not an agent application. Direct SDK calls make prompt, parameters, raw output, errors, and cost/account boundaries visible. |
| AWS data design | Diagram + concise Markdown explanation | Terraform/CDK deployment | Deployment is explicitly out of scope. The design must be clear about S3/Glue/Lambda/Athena/IAM choices without inventing operational infrastructure. |
| Diagram tooling | A versioned `design/aws_daily_pipeline.drawio` plus exported SVG/PNG | Mermaid CLI/Node toolchain | Diagram-as-code is optional here. A source `.drawio` file and committed render are easier for reviewers to open and do not add Node/npm to the runtime. If Mermaid is chosen, commit both `.mmd` source and a rendered SVG—never require a reviewer to install a renderer. |
| Packaging/automation | `uv`, Make, Git | Docker, Airflow, dbt, CI/CD | Useful in production but unnecessary for a local, seven-day dataset; use simple documented commands and real Git increments instead. |

## Minimal Commands to Document

## Sources

- [uv project layout and lockfile](https://docs.astral.sh/uv/concepts/projects/layout/) — `uv.lock` captures exact resolved versions and should be committed; [locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) — `uv sync` and `uv lock --check` behavior.
- [DuckDB Python API](https://duckdb.org/docs/stable/clients/python/overview) — current Python client version and direct JSON/Parquet querying; [DuckDB Parquet guide](https://duckdb.org/docs/stable/data/parquet/overview) — Parquet reads/writes and pushdown.
- [SQLite FTS5](https://www.sqlite.org/fts5.html) — full-text query and `bm25()` ranking.
- [PyPI DuckDB release metadata](https://pypi.org/project/duckdb/), [Boto3 release metadata](https://pypi.org/project/boto3/), [pytest release metadata](https://pypi.org/project/pytest/), and [Ruff release metadata](https://pypi.org/project/ruff/) — exact starting versions recorded above.
- [Boto3 Bedrock Runtime client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime.html) and [Boto3 `list_foundation_models`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock/client/list_foundation_models.html) — runtime and discovery APIs.
- [Amazon Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html), [API compatibility by model](https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html), and [model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) — compatibility, Region/access variability, and permissions.
- [pytest documentation](https://docs.pytest.org/en/stable/contents.html) — test framework capabilities.

## Confidence and Open Checks

| Decision area | Confidence | Reason / check before implementation |
|---|---|---|
| Python + uv | MEDIUM | Official uv documentation defines the committed lock/sync flow; choose the exact CPython patch installed on the target machine and record it. |
| DuckDB + Parquet | MEDIUM | Official DuckDB documentation directly covers the required JSON/Parquet/SQL capabilities; current PyPI metadata confirms the release used for the initial pin. |
| SQLite FTS5 KB | MEDIUM | The assessment explicitly permits SQLite FTS and SQLite documents `bm25`; add an FTS5 availability preflight test on the target Python build. |
| Test/lint tooling | MEDIUM | `pytest` and Ruff are current, minimal, and separate production dependencies from dev tooling. |
| Bedrock adapter | MEDIUM | AWS documents Boto3 runtime/control-plane operations and Converse; the code surface is intentionally tiny. |
| Selected Bedrock model ID | LOW until preflight | Model IDs, lifecycle, access, supported APIs, and Regions change. Discover and log an active compatible model in the supplied account rather than naming one in the design. |
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
