# Phase 2: Version-Aware Knowledge Base & Evaluation - Context

**Gathered:** 2026-08-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a searchable, version-aware operational knowledge base from 8 supplied Vietnamese Markdown documents using SQLite FTS5. The KB must default to current policy, keep superseded history inspectable, and pass a 10-question evaluation set with separate retrieval-hit and groundedness scoring. Include a one-page English SOP for KB updates.

Phase 2 does NOT include: Bedrock/LLM integration (Phase 3), AWS deployment, semantic/embedding search, or modification of supplied source documents.

</domain>

<decisions>
## Implementation Decisions

### Metadata Extraction
- **D-01:** Extract metadata via regex parsing of the bold `·`-delimited metadata line below each `# ` title, combined with an override table for edge cases. Regex handles common patterns (`Phiên bản X.Y`, `Ban hành: MM/YYYY`, `Cập nhật: MM/YYYY`); the override table catches fields like the approver in SOP-01 or docs that use different Vietnamese keywords.
- **D-02:** Parse `doc_id` from the filename prefix (e.g., `POL-01` from `POL-01_chinh_sach_backup_v1.md`). Parse version hint from filename suffix (`_v1`, `_v2`) when present.
- **D-03:** Represent unavailable metadata as explicit `NULL` in the SQLite schema — never invent values. Render as `"(not specified)"` in human-readable output. Follows KB-03's requirement. — **Reversibility:** reversible
- **D-04:** Keep chunk content in the original Vietnamese. Source documents are data, not authored prose — the "English throughout" constraint applies to project documentation, not to the operational content being indexed. Translation would risk semantic distortion and violate the immutable-input constraint.

### Chunking Boundaries
- **D-05:** Chunk at the `##` heading level. Each `##` section becomes one chunk, keeping numbered lists and procedures intact with their heading. Expected to produce ~20–25 chunks across 8 documents. — **Reversibility:** reversible
- **D-06:** Prepend the document-level `#` heading and bold metadata line to every chunk from that document. Each chunk is self-contained with source attribution even when read in isolation (~2 extra lines per chunk).

### Version Resolution
- **D-07:** Add an `is_current` boolean column (INTEGER 0/1) on each chunk row. Compute deterministically: for each `doc_id` family, the document with the latest `effective_date` gets `is_current=1`; earlier versions get `is_current=0`. Documents with only one version always get `is_current=1`. — **Reversibility:** costly — changing the supersession model after chunk IDs are referenced in evaluation results requires re-running the full eval.
- **D-08:** Detect the POL-01 v1→v2 supersession by parsing the Vietnamese phrase `Thay thế phiên bản trước` from the bold metadata line. When present, all earlier versions of that `doc_id` are marked `is_current=0`. Fall back to `effective_date` comparison within the same `doc_id` family when no explicit supersession phrase is found.
- **D-09:** Default queries apply `WHERE is_current=1` before FTS5 BM25 ranking (filter-then-rank). A separate query mode omits the filter for historical inspection. Two Python functions: `search_current()` and `search_all()`.

### Evaluation Design
- **D-10:** 10 predeclared evaluation questions with a 4-3-2-1 distribution across the 4 required types: 4 direct lookup, 3 multi-source synthesis, 2 version trap, 1 out-of-scope refusal.
- **D-11:** Execute all 10 evaluation questions programmatically (retrieval-only, no LLM). FTS5 retrieval recorded with ranked results and BM25 scores. KB-09 requires "at least 3" but running all 10 is cheap and gives a complete picture.
- **D-12:** Record evaluation results in both formats: structured JSON (machine-parseable, per-question fields including query, type, expected_sources, retrieved_chunks with scores, retrieval_hit, groundedness_diagnosis, overall_score) AND a rendered Markdown report for human review.
- **D-13:** Score retrieval hit and groundedness as two independent dimensions per KB-10. Retrieval hit = did the expected source chunk appear in top-k results? (pass/partial/fail). Groundedness = does the retrieved content contain the expected answer facts? (pass/partial/fail). Each scored independently per question.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Requirements
- `.planning/PROJECT.md` — Core project value and constraints
- `.planning/REQUIREMENTS.md` — KB-01 through KB-12, SOP-01, SOP-02 requirement definitions
- `.planning/ROADMAP.md` §Phase 2 — Success criteria and requirement mapping
- `.planning/STATE.md` — Current state, Phase 2 blockers

### Source Documents (8 operational docs — DO NOT MODIFY)
- `docs/onboard/datapack/data/docs/FAQ-01_loi_thuong_gap.md` — Common errors FAQ, 5 sections
- `docs/onboard/datapack/data/docs/GUIDE-01_giam_sat_he_thong.md` — System monitoring guide, dashboards + thresholds
- `docs/onboard/datapack/data/docs/POL-01_chinh_sach_backup_v1.md` — Backup policy v1 (SUPERSEDED)
- `docs/onboard/datapack/data/docs/POL-01_chinh_sach_backup_v2.md` — Backup policy v2 (CURRENT, supersedes v1)
- `docs/onboard/datapack/data/docs/POL-02_chinh_sach_truy_cap.md` — Access control policy v1.1
- `docs/onboard/datapack/data/docs/RUN-01_runbook_batch_report.md` — Batch report runbook
- `docs/onboard/datapack/data/docs/SOP-01_khoi_dong_lai_dich_vu.md` — Service restart procedure
- `docs/onboard/datapack/data/docs/SOP-02_quy_trinh_escalation.md` — Incident escalation process

### Assessment Reading Materials
- `docs/onboard/datapack/reading/01_chunking_basics.md` — Chunking strategies, metadata importance, design questions
- `docs/onboard/datapack/reading/02_rag_eval_basics.md` — RAG evaluation: retrieval hit vs groundedness, 4 eval question types, scoring criteria

### Prior Phase Context
- `.planning/phases/01-auditable-log-pipeline-analysis/01-CONTEXT.md` — Phase 1 implementation patterns (immutable inputs, explicit disposition, deterministic reruns, reviewer evidence)

### Technology Stack
- `.planning/research/STACK.md` §SQLite FTS5, §DuckDB — Stack decisions and rationale

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pipeline/__main__.py` — Stage-oriented CLI pattern with `argparse`, `--input`/`--output-root` flags. Reuse this pattern for `kb/__main__.py`.
- `pipeline/models.py` — Typed `dataclass` contracts (`Issue`, `Normalization`, `Disposition`). Reuse pattern for KB models (`Chunk`, `Document`, `EvalResult`).
- `pipeline/integrity.py` — `authorize_output_path()` symlink containment, `sha256_file()` hashing. Reuse for KB output safety and content hashing.
- `pipeline/write_outputs.py` — `write_json_atomic()`, `write_jsonl_atomic()` atomic file writing. Reuse for `kb/chunks.jsonl` and eval results.

### Established Patterns
- **Module as package:** `python -m pipeline <stage>` via `__main__.py`. KB should follow: `python -m kb <stage>`.
- **Output layout:** `data/processed/` for canonical outputs, `data/evidence/phase1/` for evidence. KB should use `data/evidence/phase2/` or similar.
- **Test layout:** `tests/pipeline/` with `pytest`, `REPOSITORY_ROOT` path resolution, `tmp_path` fixtures, parametrized validation tests.
- **Makefile targets:** `uv run --locked python -m <module> <stage>` pattern.
- **Immutable inputs:** Source files in `docs/onboard/datapack/` are never modified; `git diff --exit-code -- docs/onboard` enforces this.

### Integration Points
- `Makefile` — Add Phase 2 targets (`kb-build`, `kb-eval`, `verify-phase2`, `phase2`)
- `pyproject.toml` — No new dependencies needed (SQLite FTS5 is in Python stdlib via `sqlite3`)
- `tests/` — Add `tests/kb/` directory mirroring the pipeline test structure
- `README.md` — Extend with Phase 2 quick-start and evidence map

</code_context>

<specifics>
## Specific Ideas

- The `kb/chunks.jsonl` export (KB-04 requirement) should be deterministic and rebuildable — same input always produces same output (content-hash based).
- FTS5 `bm25()` ranking with parameter binding for safe queries — no string interpolation in SQL.
- The evaluation Markdown report should be self-contained and readable without running the code — include the query, expected answer, actual retrieved chunks, and scores inline.

</specifics>

<deferred>
## Deferred Ideas

- **Bedrock-generated answers for eval questions** — Discussed as an option but deferred to Phase 3 where Bedrock integration is scoped. Phase 2 eval is retrieval-only.
- **Semantic/embedding search** — Out of scope per stack decision; FTS5 lexical search is sufficient for 8 documents.

</deferred>

---

*Phase: 2-Version-Aware Knowledge Base & Evaluation*
*Context gathered: 2026-08-12*
