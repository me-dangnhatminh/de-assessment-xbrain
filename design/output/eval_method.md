# Evaluation Method for 3,000-Line Production Run

> **Note:** This is an evaluation METHOD document. It describes how to assess model
> performance across 3,000 log lines. It does not perform 3,000 live inferences; those
> would require separate authorization and budget.

## Evaluation Tiers

### Tier 1: Schema Validity (Automated)

Every extraction output must parse as valid JSON matching the five-field schema defined in
`design/schema.py` (`EXTRACTION_SCHEMA`). Target: **100% schema compliance**.

Automated check: `design.schema.validate_extraction()` on every output string. Any output
that fails JSON parsing or has missing/extra/wrong-typed fields is flagged for rejection.

### Tier 2: Field-Level Correctness (Automated Against Ground Truth)

Per-field precision and recall for `event_type` and `parameters` against ground truth
derived from `pipeline/normalize.py` (6 ERROR patterns with known canonical fields).

- Target: **≥95% field-level accuracy** for ERROR-class messages
- Non-ERROR ground truth: derived from observed message patterns in the 3,000-line dataset
- Metric: exact-match per field; `parameters` compared as dict equality

### Tier 3: Hallucination Detection (Automated + Human Review)

Flag any output `component`, `event_type`, or parameter value not traceable to tokens
present in the input message string.

- Target: **0% hallucination rate**
- Automated check: every value in the extraction output must be a substring of the input
  message (modulo normalization to UPPER_SNAKE_CASE for `event_type`)
- Any output failing this check is escalated to human review

## Sampling Strategy

Stratified by message pattern, proportional to frequency in the 3,000 lines.

Human review is triggered for:

- All cases with `confidence: "low"`
- All cases with `parse_status: "failed"`
- A random 5% of `confidence: "high"` results for spot-checking
