# Phase 1: Auditable Log Pipeline & Analysis - Pattern Map

**Mapped:** 2026-08-11  
**Files analyzed:** 17 planned source/config/test files (generated evidence is not source)  
**Analogs found:** 0 / 17 executable-code analogs

## Repository Baseline

This is an implementation-empty repository: `README.md` is empty and the only existing files are supplied inputs and planning/research material. Consequently, there is **no existing Python, SQL, CLI, test, configuration, or Makefile implementation to copy**. Do not treat the immutable data-pack files as code templates and do not modify them. The closest available sources are the Phase 1 research design and the supplied JSONL contract; their excerpts below are the binding starting patterns until Phase 1 establishes project code conventions.

## File Classification

| New/Modified File | Role | Data Flow | Closest available analog | Match quality |
|---|---|---|---|---|
| `pyproject.toml` | config | batch | `01-RESEARCH.md:100-116` (locked tool stack) | planning-source |
| `Makefile` | config | batch | `01-CONTEXT.md:35-39` (canonical + stage commands) | planning-source |
| `README.md` | config | batch | `01-CONTEXT.md:35-39` (reviewer evidence contract) | planning-source |
| `pipeline/__main__.py` | controller | batch | `01-RESEARCH.md:163-184` (stage CLI structure) | planning-source |
| `pipeline/models.py` | model | transform | `01-RESEARCH.md:169-173` (typed record/ledger boundary) | planning-source |
| `pipeline/integrity.py` | utility | file-I/O | `01-RESEARCH.md:144-158` (hash → manifest flow) | planning-source |
| `pipeline/ingest.py` | service | file-I/O | `01-RESEARCH.md:189-206` (line envelope before parsing) | planning-source |
| `pipeline/validation.py` | service | transform | `01-RESEARCH.md:208-212` (all issues then precedence) | planning-source |
| `pipeline/normalize.py` | utility | transform | `01-RESEARCH.md:277-288` (aware UTC conversion) | planning-source |
| `pipeline/write_outputs.py` | service | file-I/O | `01-RESEARCH.md:214-218` (stable artifacts) | planning-source |
| `pipeline/analysis.py` | service | batch | `01-RESEARCH.md:292-309` (dedicated DuckDB connection) | planning-source |
| `pipeline/sql/01_service_error_counts.sql` | utility | batch | `01-RESEARCH.md:298-306` (service ERROR aggregate) | planning-source |
| `pipeline/sql/02_daily_error_counts.sql` | utility | batch | `01-CONTEXT.md:30-34` (UTC-day rule) | planning-source |
| `pipeline/sql/03_top_normalized_errors.sql` | utility | batch | `01-CONTEXT.md:23-28` (semantic signatures) | planning-source |
| `pipeline/sql/04_quality_reconciliation.sql` | utility | batch | `01-RESEARCH.md:241-256` (line/action reconciliation) | planning-source |
| `tests/pipeline/test_validation.py` | test | transform | `01-RESEARCH.md:189-212` (parse, issue collection, precedence) | planning-source |
| `tests/pipeline/test_end_to_end.py` | test | batch | `01-RESEARCH.md:214-218,267-271` (determinism and conservation) | planning-source |

## Pattern Assignments

### `pipeline/__main__.py`, `pyproject.toml`, `Makefile`, and `README.md` (controller/config, batch)

**Closest source:** `01-RESEARCH.md:163-184`; `01-CONTEXT.md:35-39`.

Use a small stage-oriented Python CLI. The Make targets and README should expose one end-to-end command and independently runnable integrity, pipeline, analysis, and verification stages. Lock dependencies in `pyproject.toml`/`uv.lock`; use `uv ... --locked` for reviewer execution. No existing CLI or build-file syntax is available to copy.

**Structure to copy** (`01-RESEARCH.md:165-184`):

```text
pipeline/
├── __main__.py                 # stage-oriented CLI
├── integrity.py                # byte hashes and source inventory
├── ingest.py                   # line reader and source-line envelope
├── validation.py               # pure checks, issues, and final disposition
├── normalize.py                # UTC and ERROR parser
├── models.py                   # typed internal records / ledger rows
├── write_outputs.py            # atomic deterministic JSONL, Parquet, manifest writers
├── analysis.py                 # invokes checked-in SQL and writes tables
└── sql/
```

### `pipeline/models.py`, `pipeline/ingest.py`, and `pipeline/validation.py` (model/service, file-I/O/transform)

**Closest source:** `01-RESEARCH.md:189-212`; source-record examples `docs/onboard/datapack/data/app_logs_7days.jsonl:1-3,11,34,39`.

Create typed immutable/envelope and ledger-row representations. The envelope must retain source line, raw content, and input provenance before JSON parsing; malformed line 39 demonstrates why this cannot start after parsing. Validation returns every independently detected issue, then one record-level action using reject > repair > accept. Exact duplicate handling must carry the retained source line in the rejected ledger row.

**Core flow to copy** (`01-RESEARCH.md:197-206`):

```python
for source_line, raw_line in enumerate(input_file, start=1):
    try:
        record = json.loads(raw_line)
    except json.JSONDecodeError as exc:
        emit_ledger(source_line=source_line, raw_line=raw_line, error=exc)
        continue
    validate_record(source_line=source_line, record=record)
```

### `pipeline/normalize.py` (utility, transform)

**Closest source:** `01-RESEARCH.md:277-288`; data examples `app_logs_7days.jsonl:1,19`.

Parse only accepted/repairable records. Preserve raw timestamp/message; derive aware UTC instant and UTC calendar date. Apply an ERROR-only signature parser, preserving codes/components/paths as secondary fields and emitting `UNCLASSIFIED_ERROR` for otherwise valid unmatched ERROR messages. UTC conversion is normalization, not a repair.

**Timestamp pattern to copy** (`01-RESEARCH.md:280-287`):

```python
from datetime import datetime, timezone

def normalize_timestamp(raw_timestamp: str) -> datetime:
    parsed = datetime.fromisoformat(raw_timestamp)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed.astimezone(timezone.utc)
```

### `pipeline/integrity.py` and `pipeline/write_outputs.py` (utility/service, file-I/O)

**Closest source:** `01-RESEARCH.md:144-158,214-218`; immutable-input requirement `docs/onboard/datapack/README.md:16-19`.

Hash supplied inputs as bytes before and after the run, and record them in the manifest. Writers own generated paths only: stable source-line ordering, deterministic JSON key order, deterministically ordered SQL results, fixed Parquet writer configuration, and atomic replacement. Keep run-time metadata in the manifest rather than in artifacts whose hashes must be stable.

### `pipeline/analysis.py` and `pipeline/sql/*.sql` (service/utility, batch)

**Closest source:** `01-RESEARCH.md:292-309`; customer question contract `docs/onboard/01_Domain_POC.md:63-75`.

Keep all four customer calculations in static checked-in SQL files that query only cleaned Parquet. `analysis.py` supplies the file path and writes deterministic result tables; it must not reimplement aggregate calculations in Python. Each query must have explicit deterministic `ORDER BY` clauses. The daily query derives dates from the normalized UTC field; the quality query reports issue occurrences separately from final-action record totals.

**Connection/query pattern to copy** (`01-RESEARCH.md:296-306`):

```python
import duckdb

with duckdb.connect() as connection:
    rows = connection.execute(
        "SELECT service, COUNT(*) AS error_count "
        "FROM read_parquet(?) "
        "WHERE level = ? "
        "GROUP BY service "
        "ORDER BY error_count DESC, service ASC",
        [str(parquet_path), "ERROR"],
    ).fetchall()
```

### `tests/pipeline/test_validation.py` and `tests/pipeline/test_end_to_end.py` (test, transform/batch)

**Closest source:** `01-RESEARCH.md:189-218,241-271`.

Use pytest and keep fixtures outside immutable inputs. Unit tests should cover parse failure, missing required field, invalid timestamp, categorical/type/content issues, all-issue collection, precedence, exact duplicate cross-reference, UTC normalization, known and unclassified ERROR signatures. The end-to-end test should run into a temporary output directory and assert source hashes unchanged, one final action per physical line, cleaned-row conservation, expected schema/query output shape, and deterministic rerun hashes/totals.

## Shared Patterns

### Immutable input and provenance

**Source:** `docs/onboard/datapack/README.md:16-19`; `01-RESEARCH.md:189-206`.

```text
- Source log data is intentionally dirty; do not edit the original file.
- Enumerate physical lines before parsing and emit a ledger entry for parser failures.
```

Apply to `integrity.py`, `ingest.py`, `validation.py`, writers, and end-to-end tests.

### Final action and evidence boundary

**Source:** `01-CONTEXT.md:17-21`; `01-RESEARCH.md:208-218`.

```text
Collect all detected issues. Derive one final record action with:
reject > repair > accept.
Only accept/repairable analytical records reach Parquet; every source line reaches the ledger.
```

Apply to models, validation, writers, quality SQL, report rendering, and tests.

### Deterministic analytics and error handling

**Source:** `01-RESEARCH.md:214-235,292-309`.

```text
Use standard-library json/hashlib/datetime and a dedicated DuckDB connection.
Keep SQL static; parameterize values and the Parquet path; sort emitted outputs.
```

Apply to all services and SQL. There is no auth, middleware, web response, or logging framework pattern because Phase 1 is a local offline CLI.

## No Executable Analog Found

Every classified source file is new. The repository contains no application implementation, tests, SQL, package metadata, or automation configuration. The planner should use the research excerpts above as initial patterns and make the first implementation establish the project convention; it must not claim a non-existent code analog.

## Metadata

**Analog search scope:** repository root excluding `.git`, including `pipeline/`, `tests/`, configuration roots, planning, supplied brief, README, and source data  
**Files scanned:** 19 repository files plus Phase 1 planning inputs  
**Pattern extraction date:** 2026-08-11
