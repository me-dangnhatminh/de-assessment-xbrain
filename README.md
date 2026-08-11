# Xbrain Data Engineer Assessment POC

This submission-grade local proof of concept turns the supplied seven-day Sao Do Finance log into a source-preserving quality ledger, typed Parquet dataset, four reproducible SQL answers, and a directly linked reviewer report.

## Phase 1 quick start

Prerequisites are CPython 3.12–3.14, [uv](https://docs.astral.sh/uv/), GNU Make, and Git. From a clean checkout, create the exact locked environment and run the canonical workflow:

```bash
uv sync --locked
make phase1
make verify-phase1
```

`make phase1` is the canonical D-14 command. It inventories immutable inputs, generates the ledger/Parquet/schema, runs all four analyses, renders the report and manifest, and verifies the linked evidence. The Makefile uses `uv run --locked` when `uv` is on `PATH`; this repository's existing `.venv/bin/python` is only a local fallback for environments that do not expose the `uv` executable. A clean reviewer checkout should install `uv` and use the first command above.

## Independently runnable stages

All stages accept `--input`, `--output-root`, and `--max-line-bytes`; `trace` remains available for one-line provenance inspection.

```bash
uv run --locked python -m pipeline integrity --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data
uv run --locked python -m pipeline validate --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data
uv run --locked python -m pipeline run --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data
uv run --locked python -m pipeline analyze --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data
uv run --locked python -m pipeline report --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data
uv run --locked python -m pipeline verify --input docs/onboard/datapack/data/app_logs_7days.jsonl --output-root data
```

Use `all --clean` only with a generated output root. Cleanup enumerates known Phase 1 artifacts and refuses the repository root and supplied `docs/onboard` tree.

## Evidence map and findings

- `data/processed/logs_clean.parquet` is the typed analytical dataset. Parquet provides an explicit stable schema and efficient DuckDB scans while the ledger keeps raw provenance.
- `data/evidence/phase1/quality_ledger.jsonl` records every physical input line, stable issue codes, normalizations, disposition, and retained duplicate source line.
- `data/evidence/phase1/schema.json` states the fixed Parquet contract and rationale.
- `data/evidence/phase1/tables/` contains the four executable DuckDB SQL results; `pipeline/sql/` holds their parameter-bound queries.
- `data/evidence/phase1/report.md` is the primary review surface. It reads generated tables instead of recalculating customer answers.
- `data/evidence/phase1/run_manifest.json` links input inventory, hashes, commands, runtime metadata, row counts, SQL files, tables, report, and analysis IDs.

The canonical snapshot accounts for 2,923 input lines: 2,839 ACCEPT, 0 REPAIR, and 84 REJECT. Invalid JSON, invalid timestamps, missing required fields, and later exact duplicates are rejected conservatively; UTC conversion is a normalization, not a repair. `payment-api` has the highest ERROR count (139). The report identifies 2026-07-30 as the only date above the strict greater-than-two-times-median descriptive seven-day heuristic (140 errors versus a median of 27); that signal is neither a statistical anomaly result nor a causal claim. Thirty-five valid ERROR records remain `UNCLASSIFIED_ERROR` as an explicit normalization-quality warning.

## Integrity, assumptions, and boundaries

`docs/onboard/` is immutable supplied assessment material. The pipeline checks a sorted SHA-256 inventory before and after production runs, and `make verify-phase1` also requires `git diff --exit-code -- docs/onboard`.

The fixed assessment data has five observed services and three accepted levels (`INFO`, `WARN`, `ERROR`). Services are intentionally not restricted to a hard-coded allowlist because the source does not define one. The unusual-day rule is descriptive only; service contributions show distribution, not root cause. Empty-input and changed-input cases are rejected or surfaced by the explicit schema, validation, and source-integrity contracts rather than silently inferred. The POC assumes one local writer per output root; concurrent writers must use separate roots. `trace` is a single-line provenance probe, not a substitute for the full row-conservation run.

Phase 1 intentionally does not include AWS deployment, build the version-aware knowledge base, or run Bedrock extraction trials. Those later deliverables belong in `design/`, `kb/`, `sop/`, and `AI_WORKLOG.md` as subsequent phases complete.
