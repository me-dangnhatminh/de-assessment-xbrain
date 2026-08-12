# Trial Observations — Bedrock Extraction Trial

## Trial Configuration

- **Model:** `amazon.nova-lite-v1:0`
- **Region:** `ap-northeast-1`
- **Temperature:** `0.0` (deterministic)
- **Max tokens:** `512`
- **Date:** 2026-08-12
- **boto3 version:** `1.43.68`

> Note: `anthropic.claude-3-haiku-20240307-v1:0` was configured initially but returned
> `ResourceNotFoundException` with message "Access denied. This Model is marked by provider
> as Legacy and you have not been actively using the model in the last 30 days."
> `amazon.nova-lite-v1:0` was selected as the active replacement via `list_foundation_models`.

---

## Case-by-Case Results

### tc01 — PASS

**Message:** `ERR ConnTimeout db-primary after 30s retry=3`

**Model output:**
```json
{
  "event_type": "CONNECTION_TIMEOUT",
  "component": "db-primary",
  "parameters": {"retry": "3"},
  "confidence": "high",
  "parse_status": "success"
}
```

**Verdict:** PASS — all 5 fields match expected exactly. The model correctly identified
the component (`db-primary`), extracted the retry parameter, and did not include the
timeout duration (`30s`) as a parameter (it is not a key=value token).

**Latency:** 2,398 ms | **Tokens:** in=818, out=53

---

### tc02 — PASS

**Message:** `ERR PaymentDeclined txn=t811163 code=51`

**Model output:**
```json
{
  "event_type": "PAYMENT_DECLINED",
  "component": null,
  "parameters": {"txn": "t811163", "code": "51"},
  "confidence": "high",
  "parse_status": "success"
}
```

**Verdict:** PASS — correctly returned `null` for component (no named service in message),
extracted both key=value parameters, and did not fabricate a component name.

**Latency:** 456 ms | **Tokens:** in=822, out=65

---

### tc03 — PASS

**Message:** `Report row mismatch expected=843 got=759`

**Model output:**
```json
{
  "event_type": "DATA_MISMATCH",
  "component": null,
  "parameters": {"expected": "843", "got": "759"},
  "confidence": "high",
  "parse_status": "success"
}
```

**Verdict:** PASS — correctly handled a non-ERROR log level message with no ERR prefix.
Model derived `DATA_MISMATCH` from semantics (not from an explicit error prefix) and
extracted both numeric parameters correctly.

**Latency:** 413 ms | **Tokens:** in=816, out=61

---

### tc04 — FAIL

**Message:** `Retry 1/3 calling notification-worker`

**Model output:**
```json
{
  "event_type": "RETRY",
  "component": "notification-worker",
  "parameters": {"retry": "1/3"},
  "confidence": "medium",
  "parse_status": "partial"
}
```

**Expected:**
```json
{
  "parameters": {"attempt": "1", "max_attempts": "3"},
  "confidence": "medium",
  "parse_status": "partial"
}
```

**Verdict:** FAIL — `event_type`, `component`, `confidence`, and `parse_status` all match.
The only mismatch is in `parameters`: the model returned `{"retry": "1/3"}` (preserving
the fraction literally) instead of splitting `1/3` into `{"attempt":"1","max_attempts":"3"}`.

**Observation:** Both interpretations are defensible. The fraction `1/3` is present as a
single token in the message — the model preserved it verbatim (no fabrication) rather than
assuming the numerator/denominator semantics. The expected split required the model to infer
that `1/3` means "attempt 1 of 3", which is implicit domain knowledge. This is a genuine
prompt ambiguity: the extraction rules do not specify how to handle fraction-format progress
tokens. The model correctly assigned `confidence:"medium"` and `parse_status:"partial"`,
demonstrating appropriate uncertainty signaling even when the parameter structure differs.

**Latency:** 517 ms | **Tokens:** in=813, out=54

---

### tc05 — FAIL

**Message:** `Heartbeat ok`

**Model output:**
```json
{
  "event_type": "HEARTBEAT",
  "component": null,
  "parameters": {},
  "confidence": "high",
  "parse_status": "success"
}
```

**Expected:**
```json
{
  "confidence": "low",
  "parse_status": "partial"
}
```

**Verdict:** FAIL — `event_type`, `component`, and `parameters` all match perfectly (no
fabrication: `component` is `null`, `parameters` is `{}`). The mismatch is in `confidence`
and `parse_status` only: the model returned `"high"/"success"` while expected was `"low"/"partial"`.

**Observation:** The model's response is internally self-consistent — `"Heartbeat ok"` is
indeed unambiguous and the extraction is complete (no missing fields). The expected `"low"`
confidence and `"partial"` parse status were designed to test whether the model shows
appropriate caution on a minimal message with no explicit log level. The model instead made
a confident, correct extraction. This reveals a tension in the test design: the expected
values encode a conservative posture that a reasonable model need not adopt when the message
is unambiguous. No values in the output were fabricated or hallucinated.

**Latency:** 409 ms | **Tokens:** in=806, out=46

---

## Model Behavior Observations

**Schema compliance:** All 5 responses were wrapped in markdown code fences (` ```json ... ``` `)
despite the prompt instruction "Return ONLY valid JSON. No markdown, no explanation, no
surrounding text." A `_strip_code_fence()` function was added to `design/bedrock.py` to
handle this. After stripping, all 5 outputs parsed as valid JSON and passed schema validation.

**Field accuracy:** `event_type`, `component`, and `parameters` keys were all correctly
populated in 5/5 cases. The only field-level mismatches were:
- tc04: `parameters` key/value structure (fraction vs split integers)
- tc05: `confidence` and `parse_status` values (high/success vs low/partial)

**Hallucination check:** Zero hallucinated values. Every field value in every response is
traceable to tokens present in the input message string. The model explicitly returned `null`
for `component` when no named component appeared (tc02, tc03, tc05) and `{}` for `parameters`
when no key=value pairs appeared (tc05).

**Ambiguous case (tc04):** The model correctly signalled uncertainty (`confidence:"medium"`,
`parse_status:"partial"`) and did not fabricate the underlying reason for the retry. The
parameter representation difference is a prompt design issue, not a model failure.

**Edge case (tc05):** The model did not fabricate parameters for `"Heartbeat ok"` —
`parameters: {}` is correct. The confidence disagreement reflects different interpretations
of "low signal" vs "unambiguous minimal message".

---

## Honest Assessment

**Pass rate: 3/5.** The model handled clear ERROR patterns (tc01, tc02) and a non-ERROR
pattern (tc03) perfectly. For the ambiguous retry case (tc04), the model's parameter
representation is reasonable but differs from the expected split. For the minimal edge case
(tc05), the model's confident extraction is defensible — the test expected a conservative
posture the model did not adopt. Neither failing case involved fabricated or hallucinated
values, which is the most important correctness property for production use.

---

## Prompt Improvement Suggestions

1. **Code fence suppression:** Add a system prompt or stronger instruction: "Output MUST be
   raw JSON only. Do NOT wrap in markdown code blocks. Do NOT include backticks." Consider
   using a system message separate from the user message for models that support it.

2. **Fraction parameter handling (tc04):** Explicitly rule in the prompt: "If a token has
   the form `N/M` where both are integers, split into `{\"attempt\": \"N\", \"max_attempts\": \"M\"}`."

3. **Minimal message confidence calibration (tc05):** Add a rule: "If the message contains
   fewer than 3 tokens and no key=value pairs, set `confidence: \"low\"` and
   `parse_status: \"partial\"` regardless of how unambiguous the extraction appears."
