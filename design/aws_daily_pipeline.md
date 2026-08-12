# AWS Daily Log Pipeline — Architecture Explanation

> Rendered export: `aws_daily_pipeline.png`. Source: `aws_daily_pipeline.drawio` (open at https://app.diagrams.net to edit).

## Architecture Overview

The pipeline ingests a daily batch of log files from an external source into an S3 raw prefix. A Glue ETL job reads that prefix, validates records against a schema, and splits outputs: valid records are written as Parquet files to an S3 curated prefix, while records that fail validation go to an S3 quarantine prefix (dead-letter store). After writing curated data, the Glue job registers new partitions in the Glue Data Catalog. Amazon Athena uses that catalog metadata to query curated data via SQL with no loading step. CloudWatch receives job-failure alarms from Glue ETL so operators are notified without manual log polling.

## Service Justifications

- **S3 (raw prefix):** Durable, low-cost object storage for immutable raw intake. Kept separate from processed data so ETL can always be replayed.
- **Glue ETL:** Managed Apache Spark service for schema validation and format conversion. Scales automatically; integrates natively with Glue Data Catalog.
- **S3 Quarantine (dead-letter prefix):** Isolates malformed records without blocking the main pipeline. Quarantined records can be inspected and reprocessed separately.
- **S3 Curated (parquet prefix):** Stores validated data in columnar Parquet format for efficient analytical scans. Partitioned by date for cost-effective Athena queries.
- **Glue Data Catalog:** Central metadata repository storing table schemas and partition locations so Athena discovers data without manual DDL.
- **Amazon Athena:** Serverless SQL engine reading directly from S3 via the catalog. Pay-per-query pricing suits irregular analytical workloads.
- **CloudWatch:** Monitors Glue job metrics and triggers failure alarms for operational observability.

## IAM Boundaries (Least Privilege)

| Role | Permissions | Scope |
|---|---|---|
| Ingestion Role | `s3:PutObject` | Raw S3 prefix only — cannot read or modify curated/quarantine |
| Glue ETL Role | `s3:GetObject` (raw), `s3:PutObject` (curated + quarantine), `glue:*` | Scoped to specific bucket ARNs; no access to Athena results or other buckets |
| Athena Query Role | `s3:GetObject` (curated), `s3:PutObject` (results), `glue:GetTable` | Read-only on curated data; write only to a dedicated results prefix |

Each role is scoped to explicit bucket ARNs rather than `s3:*`, following least-privilege principles. No role has cross-role permissions.

## POC vs Conceptual Design

| Concern | This POC (local) | Conceptual AWS design |
|---|---|---|
| Log cleaning/validation | Python `pipeline/` package with regex-based normalization, DuckDB for analysis | Glue ETL Spark job with schema enforcement and quarantine path |
| Storage | Local filesystem and DuckDB in-memory tables | S3 Standard (raw and curated), S3 with lifecycle rules for archival |
| Query/analysis | DuckDB SQL queries on local Parquet files | Amazon Athena querying S3 via Glue Data Catalog |
| Scheduling | Manual script execution / `make` targets | EventBridge scheduled rule triggering Glue job daily |
| Monitoring | Script exit codes and stderr output | CloudWatch alarms on Glue job failure metrics, SNS notifications |

The POC validates data quality logic and query patterns locally. The AWS design replaces each local component with a managed service equivalent, preserving the same data flow.

## Uncertainties and Assumptions

1. **Ingestion trigger** — it is not decided whether the daily upload is initiated by a Lambda function, an EventBridge schedule with a Glue trigger, or a third-party push directly to S3. The choice affects IAM policy scope and retry logic.
2. **Network topology** — it is unknown whether Glue ETL must run inside a VPC (e.g., to reach a private RDS source) or can use public S3 endpoints. VPC configuration adds NAT gateway costs.
3. **Athena results bucket** — it is not confirmed whether Athena query results should land in a separate dedicated bucket or share a prefix in the curated bucket. This affects the Athena Query Role's `s3:PutObject` scope.
4. **Data volume and cost model** — actual daily log volume is unknown. Cost estimates for S3 storage class selection, Glue DPU hours, and Athena scan volume cannot be validated without production metrics.
