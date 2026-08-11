# Phase 1: Auditable Log Pipeline Review

This report renders the generated CSV tables and linked manifest metadata only; it does not query Parquet or recalculate customer aggregates.

## Method and format

The cleaned dataset uses typed Parquet because Typed Parquet keeps analytical scans reproducible while the ledger retains raw provenance.
Every physical input line is retained in the quality ledger; only ACCEPT and REPAIR records are analytical rows.

## Source integrity and quality totals

- Input lines: 2839 accepted, 0 repaired, and 84 rejected.
- The quality reconciliation table proves input-to-action and analytical-to-Parquet conservation.
- UNCLASSIFIED_ERROR warning: 35. Raw ERROR messages are retained while unmatched signatures remain a normalization-quality warning.

## 1. Service with the most ERROR records

**payment-api (139 ERROR records)** is highest in the seven-day cleaned dataset.
- Manifest analysis ID: `service-error-counts`
- SQL: `pipeline/sql/01_service_error_counts.sql`
- Result table: `evidence/phase1/tables/01_service_error_counts.csv` (5 rows)
- Cleaned dataset SHA-256: `3e5504f12c573cf34b330b8741c36c6690f1bc73b041df2fe2e8cdb2031985dc`
- Relevant row counts: accept=2839, input=2923, parquet=2839, reject=84, repair=0

## 2. Daily ERROR counts and unusual-day rule

**2026-07-30** has 140 ERROR records, a ratio of 5.185185185185185 to the seven-day median of 27.0.
It is flagged only because the count exceeds twice the median; this is a descriptive seven-day heuristic, not a statistical anomaly detector.
Service contributions are auth-service:6;batch-report:7;notification-worker:7;payment-api:112;web-portal:8; this contribution breakdown does not establish causation.
- Manifest analysis ID: `daily-error-counts`
- SQL: `pipeline/sql/02_daily_error_counts.sql`
- Result table: `evidence/phase1/tables/02_daily_error_counts.csv` (7 rows)
- Cleaned dataset SHA-256: `3e5504f12c573cf34b330b8741c36c6690f1bc73b041df2fe2e8cdb2031985dc`
- Relevant row counts: accept=2839, input=2923, parquet=2839, reject=84, repair=0

## 3. Top normalized ERROR types and services

- 1. CONNECTION_TIMEOUT: 114 ({"payment-api":114})
- 2. HTTP_502: 41 ({"web-portal":41})
- 3. NULL_POINTER: 37 ({"batch-report":37})
- Manifest analysis ID: `top-normalized-errors`
- SQL: `pipeline/sql/03_top_normalized_errors.sql`
- Result table: `evidence/phase1/tables/03_top_normalized_errors.csv` (3 rows)
- Cleaned dataset SHA-256: `3e5504f12c573cf34b330b8741c36c6690f1bc73b041df2fe2e8cdb2031985dc`
- Relevant row counts: accept=2839, input=2923, parquet=2839, reject=84, repair=0

## 4. Cleaning dispositions and issue types

- EXACT_DUPLICATE: 28 affected records (28 issue occurrences)
- JSON_MALFORMED: 18 affected records (18 issue occurrences)
- REQUIRED_FIELD_MISSING: 18 affected records (18 issue occurrences)
- TIMESTAMP_INVALID: 20 affected records (20 issue occurrences)
- Manifest analysis ID: `quality-reconciliation`
- SQL: `pipeline/sql/04_quality_reconciliation.sql`
- Result table: `evidence/phase1/tables/04_quality_reconciliation.csv` (9 rows)
- Cleaned dataset SHA-256: `3e5504f12c573cf34b330b8741c36c6690f1bc73b041df2fe2e8cdb2031985dc`
- Relevant row counts: accept=2839, input=2923, parquet=2839, reject=84, repair=0

## Limitations and scope

The unusual-day rule is descriptive only, and service contributions are evidence of distribution rather than root cause. This Phase 1 artifact does not make causal or statistical claims, deploy AWS infrastructure, or provide knowledge-base answers.
