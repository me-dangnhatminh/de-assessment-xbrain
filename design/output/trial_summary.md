# Bedrock Extraction Trial Summary

## Configuration
- **Model:** `amazon.nova-lite-v1:0`
- **Region:** `ap-northeast-1`
- **Temperature:** `0.0`
- **Max tokens:** `512`
- **Overall pass rate:** 3/5

## Results

| Case | Message | Result | Notes |
|------|---------|--------|-------|
| tc01 | ```json
{
  "event_type": "CONNECTION_TIMEOUT",
  "component": "db-primary",
  " | PASS | - |
| tc02 | ```json
{
  "event_type": "PAYMENT_DECLINED",
  "component": null,
  "parameters | PASS | - |
| tc03 | ```json
{
  "event_type": "DATA_MISMATCH",
  "component": null,
  "parameters":  | PASS | - |
| tc04 | ```json
{
  "event_type": "RETRY",
  "component": "notification-worker",
  "para | FAIL | - |
| tc05 | ```json
{
  "event_type": "HEARTBEAT",
  "component": null,
  "parameters": {},
 | FAIL | - |

## Field-Level Comparisons

### tc01 — PASS

| Field | Expected | Actual | Match |
|-------|----------|--------|-------|
| event_type | `CONNECTION_TIMEOUT` | `CONNECTION_TIMEOUT` | Y |
| component | `db-primary` | `db-primary` | Y |
| parameters | `{'retry': '3'}` | `{'retry': '3'}` | Y |
| confidence | `high` | `high` | Y |
| parse_status | `success` | `success` | Y |

### tc02 — PASS

| Field | Expected | Actual | Match |
|-------|----------|--------|-------|
| event_type | `PAYMENT_DECLINED` | `PAYMENT_DECLINED` | Y |
| component | `None` | `None` | Y |
| parameters | `{'txn': 't811163', 'code': '51'}` | `{'txn': 't811163', 'code': '51'}` | Y |
| confidence | `high` | `high` | Y |
| parse_status | `success` | `success` | Y |

### tc03 — PASS

| Field | Expected | Actual | Match |
|-------|----------|--------|-------|
| event_type | `DATA_MISMATCH` | `DATA_MISMATCH` | Y |
| component | `None` | `None` | Y |
| parameters | `{'expected': '843', 'got': '759'}` | `{'expected': '843', 'got': '759'}` | Y |
| confidence | `high` | `high` | Y |
| parse_status | `success` | `success` | Y |

### tc04 — FAIL

| Field | Expected | Actual | Match |
|-------|----------|--------|-------|
| event_type | `RETRY` | `RETRY` | Y |
| component | `notification-worker` | `notification-worker` | Y |
| parameters | `{'attempt': '1', 'max_attempts': '3'}` | `{'retry': '1/3'}` | N |
| confidence | `medium` | `medium` | Y |
| parse_status | `partial` | `partial` | Y |

### tc05 — FAIL

| Field | Expected | Actual | Match |
|-------|----------|--------|-------|
| event_type | `HEARTBEAT` | `HEARTBEAT` | Y |
| component | `None` | `None` | Y |
| parameters | `{}` | `{}` | Y |
| confidence | `low` | `high` | N |
| parse_status | `partial` | `success` | N |

---
_This report was generated from saved raw responses and is reproducible without live AWS calls._
