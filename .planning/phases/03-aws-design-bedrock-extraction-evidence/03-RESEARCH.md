---
phase: 03-aws-design-bedrock-extraction-evidence
type: research
date: 2026-08-12
---

# Phase 03 Research

## RESEARCH COMPLETE

---

## 1. AWS Architecture & Draw.io

### 1.1 AWS Service Relationships (D-02 diagram)

The required daily pipeline architecture is:

```
[Daily Source/Batch] → [raw S3 bucket] → [Glue ETL Job]
                                              ↓              ↓
                                       [quarantine S3     [curated S3 bucket]
                                        prefix/bucket]         ↓
                                         (dead-letter)    [Glue Data Catalog]
                                                               ↓
                                                           [Athena]
                                                               ↓
                                                       [CloudWatch / alerting]
```

IAM boundaries required by D-02:
- **Glue ETL Job role**: `s3:GetObject` on raw bucket, `s3:PutObject` on curated + quarantine buckets, `glue:*` for catalog operations.
- **Athena query role**: `s3:GetObject` on curated bucket, `s3:PutObject` on Athena results bucket, `glue:GetTable`/`glue:GetPartition`.
- **Ingestion role** (Lambda or EventBridge-triggered if daily): `s3:PutObject` on raw bucket only.
- Least-privilege: each role scoped to specific bucket ARNs, not `s3:*`.

Failure path annotation needed on diagram:
- Glue ETL → quarantine path (records that fail validation)
- CloudWatch alarm on Glue job failure metric

Uncertainties to annotate with `?` on the diagram (per D-03 requirement):
- Whether ingestion uses Lambda, EventBridge + Glue trigger, or AWS Batch
- Network topology (VPC or public access for Glue)
- Whether Athena outputs go to a separate S3 results bucket or the curated bucket
- Cost model assumptions (not known without actual data volumes)

### 1.2 Draw.io File Format (.drawio XML)

A `.drawio` file is a UTF-8 XML file. The minimal structure is:

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
              tooltips="1" connect="1" arrows="1" fold="1"
              page="1" pageScale="1" pageWidth="1169" pageHeight="827"
              math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <!-- shapes and connectors here, parent="1" -->
    <mxCell id="2" value="S3 Raw Bucket" style="shape=mxgraph.aws4.s3;..."
            vertex="1" parent="1">
      <mxGeometry x="100" y="100" width="78" height="78" as="geometry" />
    </mxCell>
    <mxCell id="3" value="" style="edgeStyle=orthogonalEdgeStyle;"
            edge="1" source="2" target="4" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
  </root>
</mxGraphModel>
```

Key elements:
- `mxCell id="0"` and `id="1"` are required root cells (layer structure)
- Each shape: `vertex="1"`, with `value` (label), `style`, and `mxGeometry x/y/width/height`
- Each connector: `edge="1"`, with `source` and `target` referencing cell IDs
- Groups: a container cell with `vertex="1"` and child cells with `parent="<container-id>"`
- Dashed border for IAM groups: `style="dashed=1;fillColor=none;strokeColor=#FF0000;"`
- AWS shape styles: `shape=mxgraph.aws4.s3`, `shape=mxgraph.aws4.glue`, `shape=mxgraph.aws4.athena`, `shape=mxgraph.aws4.iam_role`, `shape=mxgraph.aws4.cloudwatch`
- `?` annotation: add a plain text cell near uncertain components with `value="? assumption"` and a `callout` or `note` style

The `.drawio` file is just XML — it can be created by hand or programmatically; no special tool required to write it.

### 1.3 .drawio → PNG Export Without Desktop App

Options for producing `design/aws_daily_pipeline.png`:

**Option A (Recommended): Draw.io CLI (drawio-desktop headless)**
```bash
# If drawio desktop is installed:
drawio --export --format png --output design/aws_daily_pipeline.png design/aws_daily_pipeline.drawio
# Linux headless:
xvfb-run drawio --export --format png design/aws_daily_pipeline.drawio
```

**Option B: draw.io GitHub Action** (not applicable for local submission)

**Option C: Manual export** — Open `.drawio` file at app.diagrams.net or in the desktop app → File → Export As → PNG. This is the simplest approach for a 2-day POC. The `.drawio` source is the version-controlled artifact; the PNG is a committed rendered export.

**Option D: Plantuml or Mermaid** — Explicitly rejected by D-01.

**Decision for planning**: The PNG export is produced manually using app.diagrams.net or the Draw.io desktop app. The implementation task is to create the `.drawio` XML file programmatically (as a Python script that writes the XML, or by hand in app.diagrams.net), then export PNG manually and commit both. The `.drawio` file alone satisfies the editable-source requirement; the PNG enables reviewers without Draw.io to see the diagram.

**Practical implementation path for this POC:**
1. Write `design/aws_daily_pipeline.drawio` as XML (manually or via a small Python script that generates the XML string and writes to disk).
2. Open in app.diagrams.net (browser, no install), verify visual appearance, export PNG.
3. Commit both files.

No Python library for `.drawio` → PNG conversion exists without a browser/Electron dependency. The manual export at app.diagrams.net is the only zero-install path.

---

## 2. Boto3 Bedrock Converse API

### 2.1 Exact Python API for `bedrock-runtime` `converse()`

```python
import boto3
from botocore.exceptions import ClientError

client = boto3.client(service_name="bedrock-runtime", region_name=os.environ["AWS_REGION"])

response = client.converse(
    modelId="anthropic.claude-3-haiku-20240307-v1:0",  # or inference profile ARN
    messages=[
        {
            "role": "user",
            "content": [{"text": "your prompt here"}]
        }
    ],
    system=[
        {"text": "You are a structured data extraction assistant."}
    ],
    inferenceConfig={
        "maxTokens": 512,      # required for bounded cost
        "temperature": 0.0,    # deterministic
        "topP": 1.0,           # optional
        # "stopSequences": []  # optional
    },
    # additionalModelRequestFields={"top_k": 1}  # model-specific; optional
)
```

**Response structure:**
```python
{
    "output": {
        "message": {
            "role": "assistant",
            "content": [{"text": "...extracted JSON string..."}]
        }
    },
    "stopReason": "end_turn",  # or "max_tokens"
    "usage": {
        "inputTokens": 125,
        "outputTokens": 60,
        "totalTokens": 185
    },
    "metrics": {
        "latencyMs": 1175
    }
}
```

Extracting the text output:
```python
text = response["output"]["message"]["content"][0]["text"]
```

### 2.2 Bedrock Control Plane: `list_foundation_models()` and `get_foundation_model()`

```python
bedrock_cp = boto3.client(service_name="bedrock", region_name=os.environ["AWS_REGION"])

# List all active models in this region
response = bedrock_cp.list_foundation_models(byOutputModality="TEXT")
models = response["modelSummaries"]
# Each model has: modelId, modelName, providerName, modelLifecycle.status,
#                  inferenceTypesSupported, inputModalities, outputModalities

# Get one model's details
detail = bedrock_cp.get_foundation_model(modelIdentifier="anthropic.claude-3-haiku-20240307-v1:0")
model_info = detail["modelDetails"]
```

### 2.3 Checking if a Model Supports Converse API

The `list_foundation_models()` response includes `inferenceTypesSupported` per model. This field is a list that can contain:
- `"ON_DEMAND"` — model supports direct invocation (InvokeModel)
- `"PROVISIONED"` — model supports provisioned throughput

**Important finding**: The `inferenceTypesSupported` field does NOT directly map to Converse support. Converse compatibility is a separate capability documented at `https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html`. The practical check is:

```python
# Option 1: Attempt a minimal Converse call (preflight dry run) and check for
# ValidationException with "does not support the Converse API"
try:
    client.converse(modelId=model_id, messages=[{"role":"user","content":[{"text":"ping"}]}],
                    inferenceConfig={"maxTokens": 1})
    converse_supported = True
except client.exceptions.ValidationException as e:
    if "does not support" in str(e):
        converse_supported = False
    else:
        raise  # re-raise other validation errors

# Option 2: Use the documented compatibility table in preflight docs
```

Models confirmed to support Converse (from the API compatibility table, as of 2026-08-12):
- All Anthropic Claude 3/3.5/4.x models (Claude 3 Haiku, 3.5 Haiku, Haiku 4.5, Sonnet 4/4.5/4.6, Opus 4.x, Sonnet 5)
- Amazon Nova Micro, Lite, Pro, Premier, Nova 2 Lite
- Meta Llama 3/3.1/3.2/3.3/4 Instruct family
- Mistral family (7B, Large, Large 3, Small, Mixtral 8x7B, Pixtral Large)
- Cohere Command R, Command R+
- DeepSeek R1, V3.1, V3.2
- Most Qwen3 models

Models that do NOT support Converse:
- Embedding models (Titan Embeddings, Amazon Nova Multimodal Embeddings)
- Image generation models (Nova Canvas, Nova Reel, Stable Image family)
- Speech models (Nova Sonic)

### 2.4 Cross-Region Inference Profile ARN Format

Foundation model ID format:
```
anthropic.claude-3-haiku-20240307-v1:0
amazon.nova-lite-v1:0
meta.llama3-70b-instruct-v1:0
```

Cross-region inference profile ARN format:
```
# System-defined (predefined by AWS):
arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0

# Cross-region inference profile ID (used directly as modelId):
us.anthropic.claude-3-haiku-20240307-v1:0   # US geo
eu.anthropic.claude-3-haiku-20240307-v1:0   # EU geo
ap.anthropic.claude-3-haiku-20240307-v1:0   # APAC geo

# Application inference profile (user-created):
arn:aws:bedrock:us-east-1:123456789012:application-inference-profile/abcdefghij
```

The `BEDROCK_MODEL_ID` env variable can hold either a foundation model ID or a cross-region inference profile ID. The Converse API accepts both as `modelId`. The preflight must handle both formats.

### 2.5 `boto3.__version__` and SDK Metadata

```python
import boto3
version_str = boto3.__version__  # e.g., "1.43.68"
```

For trial metadata (D-14), capture:
```python
metadata = {
    "model_id": os.environ["BEDROCK_MODEL_ID"],
    "region": os.environ["AWS_REGION"],
    "boto3_version": boto3.__version__,
    "prompt_sha256": hashlib.sha256(prompt_text.encode()).hexdigest(),
    "request_timestamp_utc": datetime.utcnow().isoformat() + "Z",
    "response_latency_ms": response["metrics"]["latencyMs"],
    "input_tokens": response["usage"]["inputTokens"],
    "output_tokens": response["usage"]["outputTokens"],
    "stop_reason": response["stopReason"],
    "temperature": float(os.environ.get("BEDROCK_TEMPERATURE", "0.0")),
    "max_tokens": int(os.environ.get("BEDROCK_MAX_TOKENS", "512")),
}
```

**Never log**: AWS credentials, session tokens, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, account IDs from ARN parsing.

### 2.6 Standard boto3 Environment Variables

```bash
# Required for Bedrock
AWS_REGION=us-east-1              # or AWS_DEFAULT_REGION
AWS_PROFILE=my-profile            # if using named profiles
AWS_ACCESS_KEY_ID=...             # if using explicit keys (gitignored .env only)
AWS_SECRET_ACCESS_KEY=...         # never commit
AWS_SESSION_TOKEN=...             # for temporary credentials; never commit

# Phase 3 specific (in .env.example):
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_MAX_TOKENS=512
BEDROCK_TEMPERATURE=0.0
```

`.env.example` content (committed; no real values):
```
# Amazon Bedrock configuration — copy to .env and fill in real values
# .env is gitignored; never commit real credentials
AWS_REGION=us-east-1
AWS_PROFILE=
BEDROCK_MODEL_ID=
BEDROCK_MAX_TOKENS=512
BEDROCK_TEMPERATURE=0.0
```

### 2.7 ClientError Handling Pattern

```python
from botocore.exceptions import ClientError, NoCredentialsError, NoRegionError

try:
    response = client.converse(...)
except NoCredentialsError:
    # No credentials found in chain
    sys.exit("preflight fail: no AWS credentials found")
except NoRegionError:
    # AWS_REGION not set
    sys.exit("preflight fail: AWS_REGION not configured")
except ClientError as exc:
    code = exc.response["Error"]["Code"]
    message = exc.response["Error"]["Message"]
    if code == "AccessDeniedException":
        # IAM permissions missing: bedrock:InvokeModel not granted
        ...
    elif code == "ValidationException":
        # Model ID invalid or model does not support Converse
        ...
    elif code == "ResourceNotFoundException":
        # Model ID not found in this region
        ...
    elif code == "ThrottlingException":
        # Rate limit exceeded
        ...
    elif code == "ModelNotReadyException":
        # Model is not active (lifecycle status != ACTIVE)
        ...
    elif code == "ServiceUnavailableException":
        # Region/endpoint unreachable
        ...
```

The preflight should catch these codes and produce a structured diagnostic JSON:
```json
{
  "status": "fail",
  "check": "converse_api_test",
  "error_code": "AccessDeniedException",
  "message": "IAM role missing bedrock:InvokeModel permission",
  "model_id": "...",
  "region": "us-east-1"
}
```

---

## 3. Log Message Patterns & Test Case Selection

### 3.1 Log File Overview

- File: `docs/onboard/datapack/data/app_logs_7days.jsonl`
- Total lines: 2,923 (including some truncated/malformed lines)
- Lines with `"level"` field: 2,899 (some records missing the `level` field entirely — "Heartbeat ok" records)
- Services: `auth-service`, `payment-api`, `notification-worker`, `batch-report`, `web-portal`

### 3.2 All ERROR Patterns with Frequencies

| Pattern (generalized) | Count | normalize.py type |
|---|---|---|
| `ERR ConnTimeout db-primary after 30s retry=N` | 115 | `CONNECTION_TIMEOUT` |
| `ERR HTTP 502 upstream=payment-api path=/checkout` | 41 | `HTTP_502` |
| `ERR NullPointer in ReportBuilder step=aggregate` | 37 | `NULL_POINTER` |
| `ERR SMTPConnRefused host=mail-gw` | 35 | `SMTP_CONN_REFUSED` |
| `ERR AuthTokenExpired uid=uN` | 35 | `AUTH_TOKEN_EXPIRED` |
| `ERR PaymentDeclined txn=tN code=51` | 25 | `PAYMENT_DECLINED` |

### 3.3 WARN Patterns

| Pattern (generalized) | Notes |
|---|---|
| `Report row mismatch expected=N got=N` | Data-quality concern; not an ERROR itself |
| `Queue depth high depth=N` | Capacity warning; no component named |
| `Slow login Nms uid=uN` | Performance degradation; uid parameter present |
| `Slow query Nms table=tx_history` | Performance degradation; table parameter present |
| `Retry N/N calling notification-worker` | Indicates a downstream failure; ambiguous — is the retry about an error? |
| `Response time Nms path=/report` | Performance threshold |
| `Clock sync failed` | Infrastructure issue; level=WARN but timestamp="not-a-date" |

### 3.4 Selected 5 Test Cases

**TC-01: Clear ERROR — Connection Timeout (2 parameters)**

Raw message (line 19 of file, source line ~19):
```json
{"timestamp": "2026-07-27T01:54:55Z", "service": "payment-api", "level": "ERROR", "message": "ERR ConnTimeout db-primary after 30s retry=3", "request_id": "req-98843907"}
```

Input to prompt: `"ERR ConnTimeout db-primary after 30s retry=3"`

Expected output:
```json
{
  "event_type": "CONNECTION_TIMEOUT",
  "component": "db-primary",
  "parameters": {"retry": "3"},
  "confidence": "high",
  "parse_status": "success"
}
```

Rationale: Classic structured error with named component and retry parameter. Matches `normalize.py` `CONNECTION_TIMEOUT` pattern. No ambiguity.

---

**TC-02: Clear ERROR — Payment Declined (transaction + code)**

Raw message:
```json
{"timestamp": "2026-07-27T04:02:14Z", "service": "payment-api", "level": "ERROR", "message": "ERR PaymentDeclined txn=t811163 code=51", "request_id": "req-39597483"}
```

Input to prompt: `"ERR PaymentDeclined txn=t811163 code=51"`

Expected output:
```json
{
  "event_type": "PAYMENT_DECLINED",
  "component": null,
  "parameters": {"txn": "t811163", "code": "51"},
  "confidence": "high",
  "parse_status": "success"
}
```

Rationale: Transaction ID and error code are clearly extractable. `component` is null because no component name appears in this message pattern. Code=51 is an industry-standard decline code (do not fabricate what "51" means in the parameters field).

---

**TC-03: WARN — Report Row Mismatch (non-ERROR, structured parameters)**

Raw message:
```json
{"timestamp": "2026-07-27T00:53:39Z", "service": "batch-report", "level": "WARN", "message": "Report row mismatch expected=843 got=759", "request_id": "req-56751880"}
```

Input to prompt: `"Report row mismatch expected=843 got=759"`

Expected output:
```json
{
  "event_type": "DATA_MISMATCH",
  "component": null,
  "parameters": {"expected": "843", "got": "759"},
  "confidence": "high",
  "parse_status": "success"
}
```

Rationale: WARN level, not ERROR. No `ERR` prefix. The event_type must be derived from message semantics, not from a level field (which is passed separately from the message string). Tests whether the model handles WARN-level messages correctly and does not treat "report" as the component.

---

**TC-04: WARN — Retry (ambiguous/difficult case)**

Raw message:
```json
{"timestamp": "2026-07-27T00:13:20Z", "service": "payment-api", "level": "WARN", "message": "Retry 1/3 calling notification-worker", "request_id": "req-22315507"}
```

Input to prompt: `"Retry 1/3 calling notification-worker"`

Expected output:
```json
{
  "event_type": "RETRY",
  "component": "notification-worker",
  "parameters": {"attempt": "1", "max_attempts": "3"},
  "confidence": "medium",
  "parse_status": "partial"
}
```

Rationale (the "difficult case"): This is ambiguous because:
1. The message does not contain an `ERR` token — it is a retry attempt, not the error itself.
2. `notification-worker` appears as the downstream service being called, not the component reporting. This requires interpretation.
3. The fraction `1/3` encodes both `attempt` and `max_attempts` but requires splitting — a model might store it as `"1/3"` or split it. Either is defensible if the prompt rules address it; `partial` parse_status is appropriate because the retry reason (the underlying error) is absent.
4. A model might hallucinate an `error_type` or `error_code` from context — the no-fabrication rule is tested here.

---

**TC-05: Edge Case — Missing `level` field (structural anomaly)**

Raw message (entire JSON record, missing `level` key):
```json
{"timestamp": "2026-07-30T12:07:36Z", "service": "notification-worker", "message": "Heartbeat ok", "request_id": "req-48936328"}
```

Input to prompt: `"Heartbeat ok"`

Expected output:
```json
{
  "event_type": "HEARTBEAT",
  "component": null,
  "parameters": {},
  "confidence": "low",
  "parse_status": "partial"
}
```

Rationale: The message is structurally valid but:
1. There is no `level` field in the source record — this record was REJECTED in Phase 1 validation (missing required field). If the prompt receives this message in a live pipeline, the source schema is abnormal.
2. "Heartbeat ok" is a known operational message but contains no extractable parameters and no error.
3. `confidence: "low"` is appropriate because the message provides no standard event taxonomy signal.
4. Tests the prompt's handling of extremely short, parameter-free messages that are neither errors nor standard lifecycle events.

Note: The prompt should specify that it receives the `message` field value only (not the surrounding JSON envelope), so the missing `level` anomaly is implicit context rather than explicit input. The test proves the model does not fabricate parameters from an empty message.

---

## 4. AI Response Claims to Review

The full AI response text from `docs/onboard/02_AI_Proficiency.md` §Yêu cầu 2 is:

> "Bạn nên lưu toàn bộ log vào **S3 Standard-IA vì đây là lựa chọn mặc định rẻ nhất cho data lake**. Để thu dữ liệu, cấu hình một **Glue job đọc trực tiếp từ database RDS production của khách mỗi 5 phút — đây là pattern chuẩn** cho near-real-time. Dữ liệu nên chuyển sang **Parquet, một format lưu theo hàng (row-based) nên ghi rất nhanh**, phù hợp cho analytics. Với các bước transform nặng chạy khoảng **30–45 phút, dùng AWS Lambda là phù hợp nhất** vì không phải quản lý server. Về knowledge base cho RAG, hãy **chia tài liệu thành các chunk cố định 4.000 token — kích thước này luôn tốt nhất** cho mọi loại tài liệu. Cuối cùng, **không cần đánh version cho knowledge base, vì bản mới nhất luôn là bản đúng** — cứ ghi đè là được."

**The 6 misleading claims with exact quotes and corrections:**

### Claim 1: S3 storage class
**Quote:** `"S3 Standard-IA vì đây là lựa chọn mặc định rẻ nhất cho data lake"`

What is wrong: S3 Standard-IA is NOT the default storage class and NOT necessarily the cheapest for all data lake use cases. The default class is S3 Standard. Standard-IA charges retrieval fees and has a minimum 30-day storage duration — for frequently accessed hot logs it can cost MORE than Standard. S3 Intelligent-Tiering, S3 Glacier Instant Retrieval, or S3 Standard are each appropriate depending on access patterns. The "cheapest" choice is workload-dependent.

Correct replacement: "S3 Standard is the default. For a daily log pipeline, the appropriate storage class depends on retention policy and access frequency. S3 Standard for hot data, S3 Standard-IA for infrequently accessed archives (with awareness of retrieval fees), or S3 Intelligent-Tiering if access patterns are variable."

Verification source: AWS S3 storage class documentation; S3 pricing page showing minimum duration and retrieval charges.

---

### Claim 2: Glue reading directly from RDS production every 5 minutes
**Quote:** `"Glue job đọc trực tiếp từ database RDS production của khách mỗi 5 phút — đây là pattern chuẩn cho near-real-time"`

What is wrong: This is NOT a standard pattern for two reasons: (1) Glue is a batch ETL service with job startup overhead (typically 1–2+ minutes for Spark), making 5-minute intervals impractical and expensive. Glue has a minimum billed duration and cold-start time that makes sub-hourly scheduling wasteful. (2) Direct reads from a production RDS database add query load to a production system, risking performance degradation. The standard approach for near-real-time ingestion from RDS is CDC (Change Data Capture) via AWS Database Migration Service (DMS) or Amazon Kinesis Data Streams, pushing events to a queue/stream that Glue or Lambda then processes. For a daily batch pipeline (as required here), Glue on a daily schedule reading from an S3 export or via DMS snapshot is standard.

Correct replacement: "For a daily batch pipeline, Glue can read an S3 export or a DMS snapshot. For near-real-time ingestion, use CDC with DMS or Kinesis — not direct Glue polling of a production RDS every 5 minutes."

---

### Claim 3: Parquet is row-based
**Quote:** `"Parquet, một format lưu theo hàng (row-based) nên ghi rất nhanh"`

What is wrong: Parquet is COLUMNAR (column-based), not row-based. This is a fundamental factual error. Columnar storage means each column's values are stored contiguously, which enables efficient analytical queries that only read relevant columns (not all fields). Row-based formats (like CSV, JSON, Avro with default settings) write entire records contiguously, making them faster for writes but less efficient for analytical scans. Parquet's write speed advantage for analytics is its column-based encoding and compression (not "row-based writing").

Correct replacement: "Parquet is a columnar format. It excels at analytical queries that scan specific columns, with efficient compression. Row-based formats like CSV or Avro are faster for record-at-a-time ingestion; Parquet is preferred for the analytics layer because it reduces I/O for column-selective queries."

Verification source: Apache Parquet documentation; Phase 1 of this POC explicitly documented this choice with the rationale.

---

### Claim 4: Lambda for 30–45 minute transforms
**Quote:** `"30–45 phút, dùng AWS Lambda là phù hợp nhất vì không phải quản lý server"`

What is wrong: AWS Lambda has a maximum execution timeout of 15 minutes (900 seconds). A transform running 30–45 minutes CANNOT run on Lambda. The appropriate services for long-running transforms are AWS Glue (Spark-based, no timeout for long jobs), AWS Batch (for containerized jobs), or Amazon EMR. Lambda is appropriate for event-driven, short-duration processing (typically seconds to a few minutes at most).

Correct replacement: "For transforms exceeding 15 minutes, use AWS Glue (Apache Spark, no execution limit beyond Glue quotas) or AWS Batch. Lambda's maximum timeout is 15 minutes, making it unsuitable for 30–45 minute transforms."

Verification source: AWS Lambda documentation on limits (max execution time: 900 seconds); AWS Glue documentation.

---

### Claim 5: Fixed 4,000-token chunking "always best"
**Quote:** `"chia tài liệu thành các chunk cố định 4.000 token — kích thước này luôn tốt nhất cho mọi loại tài liệu"`

What is wrong: There is no universally optimal chunk size. The supplied reading `01_chunking_basics.md` explicitly states: "Không có con số đúng cho mọi trường hợp" (there is no right number for every case). 4,000 tokens is an arbitrary large chunk that risks the "chunk too large" problem — retrieving sections with irrelevant content alongside relevant content, diluting answer quality. Structure-based chunking (by heading/section) is recommended for operational documents like SOPs. Fixed-size chunking is the simplest approach but not "always best."

Correct replacement: "Chunk size depends on document type and expected queries. For operational SOPs and policy documents, structure-based chunking by section/heading preserves semantic coherence. Fixed-size chunking with overlap is a baseline, not a universal optimum. 4,000 tokens per chunk is very large and may hurt precision."

Verification source: `docs/onboard/datapack/reading/01_chunking_basics.md` (supplied reading).

---

### Claim 6: No versioning needed for knowledge base
**Quote:** `"không cần đánh version cho knowledge base, vì bản mới nhất luôn là bản đúng — cứ ghi đè là được"`

What is wrong: Version tracking is critical for operational document KB systems. The supplied reading `02_rag_eval_basics.md` explicitly identifies "bẫy phiên bản" (version trap) as a required eval category. This POC specifically identified a `POL-01` conflict between v1 and v2 — without version tracking, the KB would serve stale or incorrect policy answers. Overwriting without version history means: (1) no rollback if a document update introduces errors, (2) no ability to answer "what did the policy say before the update?", (3) no audit trail for compliance. The correct approach is to mark superseded versions as `is_current=False` while retaining them in the index for historical queries.

Correct replacement: "Version tracking is essential. Retain superseded document versions with status metadata. Apply version-aware filtering to return current-policy answers by default while keeping history accessible. Without versioning, a document update can cause the KB to serve incorrect answers with no rollback path."

Verification source: `docs/onboard/datapack/reading/02_rag_eval_basics.md` (supplied reading); Phase 2 POL-01 version conflict implementation.

---

## 5. Module Layout & CLI Design

### 5.1 Package Structure (matching `pipeline/` pattern)

```
design/
├── __init__.py          # Empty or minimal version marker
├── __main__.py          # Subcommand dispatcher (argparse), mirrors pipeline/__main__.py
├── bedrock.py           # Core Bedrock client functions: preflight(), run_trial(), build_report()
├── cases.py             # Fixed 5 test cases as Python data (not JSON file) — deterministic
├── schema.py            # JSON schema validation for extraction output
└── output/              # Generated artifacts (mostly gitignored, see section 7)
    ├── preflight_result.json          # committed if pass; gitignored if secrets
    ├── trial_summary.md               # committed
    ├── trial_observations.md          # committed
    └── responses/                     # gitignored raw Bedrock responses
        ├── tc01_raw.json
        ├── tc02_raw.json
        ├── tc03_raw.json
        ├── tc04_raw.json
        └── tc05_raw.json
```

### 5.2 `design/__main__.py` Structure

```python
"""CLI entry point for the AWS design and Bedrock extraction evidence module."""
from __future__ import annotations
import argparse
import sys

from design.bedrock import cmd_preflight, cmd_trial, cmd_report

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m design.bedrock")
    subcommands = parser.add_subparsers(dest="subcommand", required=True)
    
    preflight_parser = subcommands.add_parser(
        "preflight", help="validate Bedrock credentials, region, and model access"
    )
    preflight_parser.add_argument(
        "--output", default="design/output/preflight_result.json"
    )
    preflight_parser.set_defaults(handler=cmd_preflight)
    
    trial_parser = subcommands.add_parser(
        "trial", help="run 5 fixed extraction cases through Bedrock Converse"
    )
    trial_parser.add_argument(
        "--output-dir", default="design/output"
    )
    trial_parser.set_defaults(handler=cmd_trial)
    
    report_parser = subcommands.add_parser(
        "report", help="regenerate comparison report from saved raw responses (no API calls)"
    )
    report_parser.add_argument(
        "--output-dir", default="design/output"
    )
    report_parser.set_defaults(handler=cmd_report)
    
    return parser

def main(arguments=None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(arguments)
    try:
        return parsed.handler(parsed)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
```

CLI invocations:
```bash
uv run python -m design.bedrock preflight
uv run python -m design.bedrock trial
uv run python -m design.bedrock report
```

### 5.3 `design/bedrock.py` Key Functions

```python
def cmd_preflight(args) -> int:
    """
    Validates: AWS_REGION set → boto3 client can be created → Region reachable
    → list_foundation_models() succeeds → configured model ID exists in response
    → minimal Converse call succeeds with 1 token.
    Writes structured JSON to args.output. Exits 0 (pass) or 1 (fail).
    """

def cmd_trial(args) -> int:
    """
    Refuses to run if no recent passing preflight result exists (check args.output_dir/preflight_result.json).
    Loads 5 cases from design/cases.py.
    For each case: sends Converse request, saves raw response JSON, validates output schema,
    produces expected-vs-actual comparison.
    Writes: design/output/responses/tcNN_raw.json, design/output/trial_summary.md,
            design/output/trial_observations.md.
    """

def cmd_report(args) -> int:
    """
    Reads existing design/output/responses/tcNN_raw.json files without making API calls.
    Regenerates comparison tables and trial_summary.md.
    Deterministic: same inputs → same outputs.
    """
```

### 5.4 `design/cases.py` Structure

```python
"""Fixed extraction test cases — deterministic, no file I/O."""

from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class TestCase:
    case_id: str
    message: str          # raw message string passed to prompt
    expected: dict        # expected JSON output dict
    note: str             # brief description of what makes this case interesting

CASES: tuple[TestCase, ...] = (
    TestCase(
        case_id="tc01",
        message="ERR ConnTimeout db-primary after 30s retry=3",
        expected={
            "event_type": "CONNECTION_TIMEOUT",
            "component": "db-primary",
            "parameters": {"retry": "3"},
            "confidence": "high",
            "parse_status": "success",
        },
        note="Clear ERROR with named component and retry parameter",
    ),
    # ... tc02 through tc05
)
```

### 5.5 `design/schema.py` Structure

```python
"""JSON schema validation for extraction output."""

EXTRACTION_SCHEMA = {
    "type": "object",
    "required": ["event_type", "component", "parameters", "confidence", "parse_status"],
    "properties": {
        "event_type": {"type": "string"},
        "component": {"type": ["string", "null"]},
        "parameters": {"type": "object"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "parse_status": {"type": "string", "enum": ["success", "partial", "failed"]},
    },
    "additionalProperties": False,
}

def validate_extraction(data: dict) -> list[str]:
    """Return a list of validation error strings; empty list = valid."""
    ...
```

---

## 6. Testing Strategy

### 6.1 Testing Bedrock Integration Without Live Calls

Use `unittest.mock.patch` to replace the boto3 client. This is the same pattern used throughout the pipeline tests.

```python
# tests/design/test_bedrock.py
from unittest.mock import MagicMock, patch
import json

def make_mock_converse_response(text: str) -> dict:
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": "end_turn",
        "usage": {"inputTokens": 50, "outputTokens": 30, "totalTokens": 80},
        "metrics": {"latencyMs": 500},
    }

@patch("boto3.client")
def test_trial_parses_valid_response(mock_boto3_client):
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client
    valid_json = json.dumps({
        "event_type": "CONNECTION_TIMEOUT",
        "component": "db-primary",
        "parameters": {"retry": "3"},
        "confidence": "high",
        "parse_status": "success",
    })
    mock_client.converse.return_value = make_mock_converse_response(valid_json)
    # call trial logic, assert pass/fail diagnosis = PASS
    ...
```

### 6.2 Required Tests per Component

**Preflight tests (no live calls):**
- `test_preflight_missing_region_env_var` — exits 1, writes fail JSON
- `test_preflight_access_denied` — ClientError AccessDeniedException → fail JSON with diagnostic
- `test_preflight_model_not_found` — ResourceNotFoundException → fail JSON
- `test_preflight_converse_not_supported` — ValidationException → fail JSON
- `test_preflight_success` — all checks pass → writes pass JSON with metadata, returns 0

**Trial runner tests:**
- `test_trial_refuses_without_passing_preflight` — exits 1 if no preflight_result.json or status != "pass"
- `test_trial_saves_raw_response` — each case writes a `tcNN_raw.json` file
- `test_trial_validates_schema` — parses model output as JSON, validates against schema
- `test_trial_expected_vs_actual_comparison` — compares each field against expected output
- `test_trial_handles_invalid_json_output` — model returns non-JSON → parse_status="failed", no crash
- `test_trial_records_metadata` — boto3.__version__, timestamp, token counts in output

**Report generator tests:**
- `test_report_is_deterministic` — running report twice on same saved responses produces same output
- `test_report_without_api_calls` — boto3.client is never called during `report` command
- `test_report_reads_saved_responses` — regenerates comparison from `tcNN_raw.json` files

**Schema validation tests:**
- `test_schema_valid_full_object`
- `test_schema_rejects_missing_field`
- `test_schema_rejects_unknown_field` (additionalProperties = False)
- `test_schema_rejects_invalid_confidence_value`
- `test_schema_rejects_null_event_type`

### 6.3 Test File Location

```
tests/
├── design/
│   ├── __init__.py
│   ├── test_bedrock.py       # preflight + trial + report CLI commands
│   ├── test_schema.py        # extraction JSON schema validation
│   └── test_cases.py         # fixture integrity: 5 cases, all fields present
```

---

## 7. File Layout & Gitignore Plan

### 7.1 Files to Create

```
design/
├── __init__.py
├── __main__.py                            # re-exports or delegates to bedrock.py commands
├── bedrock.py                             # preflight, trial, report logic
├── cases.py                               # 5 fixed test cases
├── schema.py                              # JSON schema + validation
├── aws_daily_pipeline.drawio              # COMMITTED — editable diagram source (XML)
├── aws_daily_pipeline.png                 # COMMITTED — rendered export for reviewers
├── aws_daily_pipeline.md                  # COMMITTED — ≤1-page English explanation
├── ai_response_review.md                  # COMMITTED — ≤1-page English review of 6 claims
├── extraction_prompt.md                   # COMMITTED — ≤2-page structured prompt + eval method
└── output/
    ├── preflight_result.json              # COMMITTED — non-secret pass result
    ├── trial_summary.md                   # COMMITTED — comparison table + pass/fail
    ├── trial_observations.md              # COMMITTED — honest model behavior notes
    └── responses/                         # GITIGNORED — raw Bedrock responses
        ├── tc01_raw.json
        ├── tc02_raw.json
        ├── tc03_raw.json
        ├── tc04_raw.json
        └── tc05_raw.json
```

Root-level files:
```
.env.example                               # COMMITTED — placeholder keys only
.env                                       # GITIGNORED — real credentials
```

### 7.2 Gitignore Additions Needed

Add to `.gitignore`:
```
# Bedrock trial raw responses (may contain model output that is not independently verifiable)
design/output/responses/
# Local environment with real credentials
.env
# Python bytecode (already present)
__pycache__/
*.py[cod]
```

**Committed vs Gitignored rationale:**
- `preflight_result.json` → COMMITTED: contains no secrets (model ID, region, boto3 version, timestamps — all non-secret metadata); lets reviewers verify the preflight passed without re-running.
- `responses/tcNN_raw.json` → GITIGNORED by default but the implementer SHOULD commit them. Per D-13, the raw responses are required evidence (AIEXT-08: "reviewer can inspect each raw Bedrock response"). However, they may contain model output of unknown character; the safe default is gitignore with a note in README to run the trial and commit responses. Alternatively: commit the raw responses since they contain no credentials and are model output, not secrets.
- **Recommendation for planner**: Commit `design/output/responses/*.json` to satisfy AIEXT-07/08/10. They contain no secrets. Add a comment in `.gitignore` that explains the override. Use `git add -f design/output/responses/` after trial run.

### 7.3 `.env.example` (exact content)

```
# Amazon Bedrock configuration for Phase 3 Bedrock trial
# Copy this file to .env and fill in real values
# NEVER commit .env — it is gitignored

# AWS region where Bedrock is available (required)
AWS_REGION=us-east-1

# AWS profile to use (optional; uses default credential chain if empty)
AWS_PROFILE=

# The Bedrock model ID or cross-region inference profile ID to use for extraction trials
# Examples:
#   anthropic.claude-3-haiku-20240307-v1:0
#   us.anthropic.claude-3-haiku-20240307-v1:0  (cross-region US geo)
#   amazon.nova-micro-v1:0
BEDROCK_MODEL_ID=

# Maximum output tokens per Converse request (default: 512)
BEDROCK_MAX_TOKENS=512

# Temperature for inference (0.0 = deterministic; default: 0.0)
BEDROCK_TEMPERATURE=0.0
```

---

## 8. Key Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Configured Bedrock model not available in the account/region | HIGH | HIGH | Preflight validates this before trial; exit 1 with clear diagnostic; doc says "configure a model accessible in your account" |
| Model does not support Converse API | MEDIUM | HIGH | Preflight catches ValidationException; list of Converse-compatible models documented in RESEARCH |
| Model output is not valid JSON (fails schema) | MEDIUM | MEDIUM | Trial code wraps JSON parsing in try/except; marks as `parse_status="failed"` without crashing; report command re-reads saved raw response |
| No AWS credentials available in reviewer's environment | HIGH | MEDIUM | Preflight provides clear error; `report` command works offline with saved responses; all local tasks run without AWS |
| Draw.io PNG export requires manual step | LOW | LOW | Document the step; `.drawio` XML alone is the authoritative artifact; app.diagrams.net requires no install |
| Temperature > 0 causes non-deterministic trial results | LOW | LOW | Default `BEDROCK_TEMPERATURE=0.0`; `report` command is deterministic from saved raw responses regardless |
| `boto3` not in pyproject.toml dependencies | HIGH | HIGH | Must add `boto3==1.43.68` (or latest stable) to `[project] dependencies` in `pyproject.toml`; currently missing |
| Real AWS account ID leaking through ARN parsing/logging | LOW | HIGH | Never log response ARNs, account IDs, or session tokens; preflight metadata explicitly lists safe fields only |

---

## 9. Planning Recommendations

### For PLAN.md creation, the planner should know:

**Task sequencing:**
1. Add `boto3` to `pyproject.toml` dependencies and run `uv lock` — this is a BLOCKER for all Bedrock work.
2. Create `design/` package structure (5 Python files) before writing any Markdown artifacts — code and tests can proceed in parallel with diagram authoring.
3. AWS diagram (`aws_daily_pipeline.drawio` + PNG) can be done independently of Bedrock code.
4. The `extraction_prompt.md` document must be finalized before the trial can run (it contains the prompt text).
5. The 5 test cases in `cases.py` must be finalized before writing `extraction_prompt.md` (test cases inform prompt design).
6. `design/ai_response_review.md` is independent of all code — pure writing task.

**Exact function signatures the planner should use as acceptance criteria:**

`design/bedrock.py`:
- `def run_preflight(region: str, model_id: str) -> dict` — returns structured result dict
- `def run_trial_case(client, model_id: str, prompt: str, max_tokens: int, temperature: float) -> dict` — returns raw Converse response dict + timing
- `def validate_extraction_output(raw_text: str) -> tuple[dict | None, list[str]]` — returns (parsed dict or None, list of errors)
- `def compare_case(case: TestCase, actual: dict | None) -> dict` — returns field-level comparison

**Output file paths (absolute, for tasks):**
- `/mnt/data/Minh/Coding/de-assessment-xbrain/design/aws_daily_pipeline.drawio`
- `/mnt/data/Minh/Coding/de-assessment-xbrain/design/aws_daily_pipeline.png`
- `/mnt/data/Minh/Coding/de-assessment-xbrain/design/aws_daily_pipeline.md`
- `/mnt/data/Minh/Coding/de-assessment-xbrain/design/ai_response_review.md`
- `/mnt/data/Minh/Coding/de-assessment-xbrain/design/extraction_prompt.md`
- `/mnt/data/Minh/Coding/de-assessment-xbrain/design/output/preflight_result.json`
- `/mnt/data/Minh/Coding/de-assessment-xbrain/design/output/trial_summary.md`
- `/mnt/data/Minh/Coding/de-assessment-xbrain/design/output/trial_observations.md`
- `/mnt/data/Minh/Coding/de-assessment-xbrain/design/output/responses/tc{01-05}_raw.json`
- `/mnt/data/Minh/Coding/de-assessment-xbrain/.env.example`

**pyproject.toml change required:**
```toml
dependencies = [
    "boto3==1.43.68",   # ADD THIS
    "duckdb==1.5.5",
]
```

**Makefile targets to add:**
```makefile
design-preflight: sync
    $(PYTHON) -m design.bedrock preflight

design-trial: sync
    $(PYTHON) -m design.bedrock trial

design-report:
    $(PYTHON) -m design.bedrock report

phase3: design-preflight design-trial design-report
```

**Verification gate for AIEXT-10:**
The `report` command must produce identical output when run twice on the same saved `tcNN_raw.json` files. Test this with `git diff` after a second `report` run.

**The diagram PNG cannot be generated programmatically without a browser/Electron install.** The plan must include a manual step: "Open `design/aws_daily_pipeline.drawio` in app.diagrams.net, export PNG, save as `design/aws_daily_pipeline.png`, commit." This step should be in the plan as a human action item.

**Converse API permission required:** The IAM policy for the Bedrock trial must include `bedrock:InvokeModel` (not `bedrock:Converse` — the permission is `bedrock:InvokeModel` for Converse calls). Preflight should check for this.

**Suggested plan split (2 plans):**
- Plan 03-01: AWS architecture diagram + English explanation + AI response review (pure writing/diagram; no code; no AWS access needed)
- Plan 03-02: Extraction prompt document + Bedrock Python module (preflight, trial, report) + tests + `.env.example` + Makefile updates

This split allows Plan 03-01 to be reviewed and corrected independently of the code, and lets Plan 03-02 be blocked only by the account-specific Bedrock access confirmation.
