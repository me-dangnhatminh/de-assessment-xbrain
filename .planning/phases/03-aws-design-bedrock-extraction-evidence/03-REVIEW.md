---
phase: 03-aws-design-bedrock-extraction-evidence
reviewed: 2026-08-12T11:47:28Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - design/__init__.py
  - design/__main__.py
  - design/bedrock.py
  - design/cases.py
  - design/schema.py
  - design/extraction_prompt.md
  - design/aws_daily_pipeline.md
  - design/ai_response_review.md
  - design/output/eval_method.md
  - design/output/trial_summary.md
  - design/output/trial_observations.md
  - tests/design/test_bedrock.py
  - tests/design/test_cases.py
  - tests/design/test_schema.py
  - Makefile
  - pyproject.toml
  - .env.example
findings:
  critical: 1
  warning: 2
  info: 4
  total: 7
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-08-12T11:47:28Z  **Depth:** standard  **Files Reviewed:** 17  **Status:** issues_found

## Summary

The extraction schema, validator, fixed test cases, and the Bedrock Converse adapter are
small, well-structured, and the 23 unit tests pass. The core validation and comparison
logic is correct against the stated schema. However, the documented/automated command
surface is broken at the entry point: the Makefile `phase3`/`design-*` targets invoke
`python -m design.bedrock`, but `design/bedrock.py` has no `if __name__ == "__main__"`
guard, so those commands silently no-op and exit 0 (verified). The only working entry point
is `python -m design` via `design/__main__.py`. This makes every documented Phase 3 command
and `make phase3` non-functional, which is a shipping blocker. Additional findings concern
markdown-report robustness and validation-diagnostic completeness.

## Critical Issues

### CR-01: Makefile / documented CLI entry point silently no-ops (make phase3 does nothing)

**File:** `Makefile` lines 80-89; `design/bedrock.py` (no `__main__` guard)

**Issue:** `design/__main__.py` (the real CLI, reached via `python -m design`) dispatches the
subcommands and calls the handlers. But the Makefile targets and the argparse `prog` string
invoke `python -m design.bedrock <subcommand>`, which executes `design/bedrock.py` directly.
That module contains only imports and function definitions — there is no
`if __name__ == "__main__":` block and no argparse call. Verified empirically:

```
$ .venv/bin/python -m design.bedrock preflight
$ echo $?    # -> 0, no output, no preflight_result.json written
```

Because the module imports cleanly and exits 0, `make design-preflight`, `make design-trial`,
`make design-report`, and `make phase3` all appear to succeed while doing nothing and writing
no artifacts. (The `if __name__ == "__main__"` guard in `__main__.py` does not help, because
`python -m design.bedrock` loads `design/bedrock.py`, not `design/__main__.py`.) This defeats
the reproducible-evidence requirement of the milestone.

**Fix:** Add a proper entry point to `design/bedrock.py` so the documented
`python -m design.bedrock <subcommand>` form works, e.g.:

```python
def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="python -m design.bedrock", description="...")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, handler in (
        ("preflight", cmd_preflight),
        ("trial", cmd_trial),
        ("report", cmd_report),
    ):
        p = sub.add_parser(name)
        p.add_argument("--output-dir", default="design/output")
        p.set_defaults(handler=handler)
    args = parser.parse_args()
    return args.handler(args)

if __name__ == "__main__":
    raise SystemExit(main())
```

Alternatively (and less ideally), update the Makefile to `$(PYTHON) -m design preflight` etc.,
and align the `prog` string in `design/__main__.py`. Recommend the first option to match the
documented `python -m design.bedrock` invocation and the Makefile.

## Warnings

### WR-01: Trial summary Markdown tables are corrupted by unescaped newlines in the response text

**File:** `design/bedrock.py` — `_write_trial_summary`, lines 440-444

**Issue:** The `msg` cell is truncated to 80 chars and only `|` is escaped with `\|`
(line 441). It is not normalized for newlines (or backticks). Bedrock consistently returns the
JSON wrapped in markdown code fences, so `response_text` contains literal newlines. These
newlines break the Markdown table rows, as visibly confirmed in the committed
`design/output/trial_summary.md` (e.g. the `tc01` row spills across multiple lines and embeds
raw ` ```json `/`{`). The generated report is therefore not valid Markdown and is hard to
read/automate.

**Fix:** Normalize the cell content before writing, e.g.:

```python
msg = c.get("response_text", "").replace("\n", " ").replace("|", "\\|")[:80]
```

### WR-02: `validate_extraction` returns on the first error class, skipping type checks when only extra fields are present

**File:** `design/schema.py` — `validate_extraction`, lines 43-45

**Issue:** The early return `if errors: return errors` is gated on *any* error, not just missing
required keys (the comment on line 43 says "If missing keys, skip type checks"). Because the
extra-key check (lines 39-41) runs before the early return, a record that has all five required
keys present but ALSO an unexpected field, AND a wrong-typed value (e.g. `confidence: 7`), will
return only `["unexpected fields: ['extra']"]` and never report the bad `confidence` type. The
pass/fail decision is still correct, but the diagnostics are incomplete and can cause a reviewer
to fix the extra field and be surprised by a second round of errors. This is a robustness defect
in the validator the trial relies on.

**Fix:** Defer the early return to after the type checks, or only skip type checks when a
*required* key is missing:

```python
missing = [k for k in _REQUIRED_KEYS if k not in data]
if missing:
    return errors + [f"missing required field: {k!r}" for k in missing]
# ... extra-key and type checks accumulate into errors ...
return errors
```

## Info

### IN-01: Validation is performed twice per case; `_validation_errors` is computed but unused

**File:** `design/bedrock.py` lines 350-352 and 172-204

**Issue:** In `cmd_trial`, `validate_extraction_output(response_text)` is called and its error
result is discarded (`parsed, _validation_errors = ...`), then `compare_case` calls
`validate_extraction(actual)` again. The redundant call and the dead `_validation_errors`
variable add noise and a second parse/validate pass with no effect. Consider dropping the
`validate_extraction_output` call in `cmd_trial` and letting `compare_case` own validation, or
have `compare_case` accept the already-computed errors.

### IN-02: `_read_env` helper is defined but never used

**File:** `design/bedrock.py` lines 25-32

**Issue:** `_read_env` is dead code. All call sites read `os.environ.get(...).strip()` and
inline their own error handling (e.g. `cmd_preflight`/`cmd_trial`). Remove the helper or use it
consistently.

### IN-03: Broad `except Exception` in `run_preflight` and `run_trial_case` masks programming errors

**File:** `design/bedrock.py` lines 106-114 and 137-138

**Issue:** Both catch-all handlers convert any exception (including genuine programming errors
such as a `TypeError` from a bad argument) into a `status: "fail"` / `{"error": ...}` result.
This is acceptable for a CLI preflight/trial, but it can hide bugs as "validation failures" in
the saved artifacts. Consider re-raising unexpected non-boto3 exceptions in debug mode, or at
least logging the full traceback.

### IN-04: `run_trial_case` error details are not surfaced in the comparison summary

**File:** `design/bedrock.py` lines 137-138, 350-354

**Issue:** On a client error, `run_trial_case` returns `{"error": str(exc), "output": None,
"_latency_ms": 0}`. The error string is preserved in the saved raw file, but the summary table's
"Notes" column only shows `validation_errors` ("output was not valid JSON"), so a reviewer
reading `trial_summary.md` cannot tell a throttling/permission failure from a genuinely
malformed model output. Consider carrying the request error into the comparison/notes.

---
_Reviewed:_ _Reviewer: gsd-code-reviewer_ _Depth: standard_