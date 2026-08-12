---
plan: 03-03
status: complete
completed_at: 2026-08-12T11:00:00Z
commit: 461c0a9fabb5ea5b96376af0a85dc4d506e13a82
---

# Summary: Plan 03-03

## Trial Configuration

- **Model:** `amazon.nova-lite-v1:0` (Claude 3 Haiku was Legacy/unavailable; Nova Lite selected via `list_foundation_models`)
- **Region:** `ap-northeast-1`
- **Temperature:** `0.0`, **Max tokens:** `512`
- **boto3:** `1.43.68`

## Artifacts Produced

- `design/output/preflight_result.json` — status:pass, non-secret metadata only
- `design/output/responses/tc01_raw.json` — PASS (CONNECTION_TIMEOUT, db-primary, retry=3)
- `design/output/responses/tc02_raw.json` — PASS (PAYMENT_DECLINED, null, txn+code)
- `design/output/responses/tc03_raw.json` — PASS (DATA_MISMATCH, null, expected+got)
- `design/output/responses/tc04_raw.json` — FAIL (RETRY: fraction {retry:"1/3"} vs split {attempt,max_attempts})
- `design/output/responses/tc05_raw.json` — FAIL (HEARTBEAT: confidence high vs low, parse_status success vs partial)
- `design/output/trial_summary.md` — expected-vs-actual table, field-level results, 3/5 pass rate
- `design/output/trial_observations.md` — honest per-case analysis, schema compliance, hallucination check, prompt improvements

## Verification

- Preflight: `status:pass` ✓
- Trial pass rate: **3/5** (tc01, tc02, tc03 pass; tc04, tc05 fail — both honest, no hallucination)
- Secret scan: 0 credentials/account IDs in committed files ✓
- `python -m design.bedrock report` with invalid AWS_REGION: exits 0, no API calls ✓
- Report determinism: byte-identical on two consecutive runs (`diff` empty) ✓
- `pytest -q` (full suite): 201 passed, 0 failures ✓
- Code fence fix: `_strip_code_fence()` added to handle Nova Lite markdown wrapping

## Notable Findings

- Nova Lite consistently wraps JSON in markdown fences despite "plain JSON only" instruction — prompt improvement documented
- tc04: parameter fraction representation is defensible, not a hallucination — prompt ambiguity identified
- tc05: model's high confidence on "Heartbeat ok" is internally consistent — test design tension documented
- Zero hallucinated values across all 5 responses
