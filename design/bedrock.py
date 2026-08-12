"""Amazon Bedrock client logic for Phase 3 extraction trial."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import sys
from typing import Any

import boto3
import botocore.exceptions

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _read_env(name: str) -> str:
    """Return env var value or raise SystemExit with a helpful message."""
    val = os.environ.get(name, "").strip()
    if not val:
        print(f"ERROR: environment variable {name!r} is not set or is empty.", file=sys.stderr)
        print(f"  Copy .env.example to .env and set {name}.", file=sys.stderr)
        raise SystemExit(1)
    return val


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def run_preflight(region: str, model_id: str) -> dict[str, Any]:
    """Validate AWS region, credentials, and model Converse access.

    Returns a result dict with 'status': 'pass' or 'fail'.
    """
    if not region:
        return {
            "status": "fail",
            "check": "region",
            "error_code": "NoRegionError",
            "message": "AWS_REGION is empty; set it in .env",
            "model_id": model_id,
            "region": region,
        }

    try:
        client = boto3.client("bedrock-runtime", region_name=region)
        client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": "ping"}]}],
            inferenceConfig={"maxTokens": 1},
        )
        return {
            "status": "pass",
            "model_id": model_id,
            "region": region,
            "boto3_version": boto3.__version__,
            "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
        }
    except botocore.exceptions.NoCredentialsError:
        return {
            "status": "fail",
            "check": "credentials",
            "error_code": "NoCredentialsError",
            "message": "No AWS credentials found in credential chain",
            "model_id": model_id,
            "region": region,
        }
    except botocore.exceptions.NoRegionError:
        return {
            "status": "fail",
            "check": "region",
            "error_code": "NoRegionError",
            "message": "No region configured",
            "model_id": model_id,
            "region": region,
        }
    except botocore.exceptions.ClientError as exc:
        code = exc.response["Error"]["Code"]
        msg = exc.response["Error"].get("Message", str(exc))
        if code == "AccessDeniedException":
            check = "iam_permissions"
        elif code == "ResourceNotFoundException":
            check = "model_not_found"
        elif code == "ValidationException" and "does not support" in msg:
            check = "converse_not_supported"
        else:
            check = "api_error"
        return {
            "status": "fail",
            "check": check,
            "error_code": code,
            "message": msg,
            "model_id": model_id,
            "region": region,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "fail",
            "check": "unknown",
            "error_code": type(exc).__name__,
            "message": str(exc),
            "model_id": model_id,
            "region": region,
        }


def run_trial_case(
    client: Any,
    model_id: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    """Invoke Bedrock Converse for one test case and return the full response plus metadata."""
    import time

    start = time.monotonic()
    try:
        response = client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        response["_latency_ms"] = latency_ms
        return response
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "output": None, "_latency_ms": 0}


def _strip_code_fence(text: str) -> str:
    """Strip markdown code fences (```json ... ``` or ``` ... ```) from model output."""
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence line (e.g. ```json or ```)
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        # Remove closing fence
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3].rstrip()
    return text.strip()


def validate_extraction_output(raw_text: str) -> tuple[dict[str, Any] | None, list[str]]:
    """Parse *raw_text* as JSON and validate against EXTRACTION_SCHEMA.

    Strips markdown code fences before parsing — handles models that wrap
    JSON in ```json ... ``` despite instructions to return plain JSON.
    """
    from design.schema import validate_extraction

    cleaned = _strip_code_fence(raw_text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None, ["output is not valid JSON"]
    errors = validate_extraction(parsed)
    return parsed, errors


def compare_case(case: Any, actual: dict[str, Any] | None) -> dict[str, Any]:
    """Compare actual extraction output against case.expected."""
    from design.schema import validate_extraction

    validation_errors: list[str] = []
    if actual is None:
        validation_errors = ["output was not valid JSON"]

    field_results = []
    if actual is not None:
        validation_errors = validate_extraction(actual)
        for field, expected_val in case.expected.items():
            actual_val = actual.get(field)
            field_results.append(
                {
                    "field": field,
                    "expected": expected_val,
                    "actual": actual_val,
                    "match": actual_val == expected_val,
                }
            )

    overall = (
        "pass"
        if actual is not None and not validation_errors and all(fr["match"] for fr in field_results)
        else "fail"
    )
    return {
        "case_id": case.case_id,
        "overall": overall,
        "field_results": field_results,
        "validation_errors": validation_errors,
    }


def _build_prompt(message: str, extraction_prompt_path: str = "design/extraction_prompt.md") -> str:
    """Build a Converse prompt combining the extraction role/rules and the message."""
    prompt_path = pathlib.Path(extraction_prompt_path)
    if prompt_path.exists():
        instructions = prompt_path.read_text(encoding="utf-8")
    else:
        instructions = (
            "Extract event_type, component, parameters, confidence, and parse_status from the "
            "log message. Return ONLY valid JSON with no surrounding text."
        )
    return f"{instructions}\n\nLog message: {message}"


def _extract_response_text(response: dict[str, Any]) -> str:
    """Pull the assistant text out of a Converse response dict."""
    try:
        return response["output"]["message"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return ""


# ---------------------------------------------------------------------------
# CLI command handlers
# ---------------------------------------------------------------------------


def cmd_preflight(args: Any) -> int:
    """Handle: python -m design.bedrock preflight"""
    region = os.environ.get("AWS_REGION", "").strip()
    model_id = os.environ.get("BEDROCK_MODEL_ID", "").strip()

    if not region:
        print(
            "ERROR: AWS_REGION is not set. Copy .env.example to .env and configure it.",
            file=sys.stderr,
        )
        return 1
    if not model_id:
        print(
            "ERROR: BEDROCK_MODEL_ID is not set. Copy .env.example to .env and configure it.",
            file=sys.stderr,
        )
        return 1

    print(f"Running preflight: region={region!r}, model_id={model_id!r}")
    result = run_preflight(region, model_id)

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Preflight result written to {output_path}")

    if result["status"] == "pass":
        print("Preflight PASSED")
        return 0
    else:
        print(
            f"Preflight FAILED: check={result.get('check')}, error={result.get('message')}",
            file=sys.stderr,
        )
        return 1


def cmd_trial(args: Any) -> int:
    """Handle: python -m design.bedrock trial"""
    region = os.environ.get("AWS_REGION", "").strip()
    model_id = os.environ.get("BEDROCK_MODEL_ID", "").strip()
    max_tokens = int(os.environ.get("BEDROCK_MAX_TOKENS", "512"))
    temperature = float(os.environ.get("BEDROCK_TEMPERATURE", "0.0"))

    if not region or not model_id:
        print("ERROR: AWS_REGION and BEDROCK_MODEL_ID must be set in .env", file=sys.stderr)
        return 1

    output_dir = pathlib.Path(args.output_dir)
    preflight_path = output_dir / "preflight_result.json"

    if not preflight_path.exists():
        print(
            f"ERROR: preflight required — {preflight_path} not found.\n"
            "Run: python -m design.bedrock preflight",
            file=sys.stderr,
        )
        return 1

    preflight_data = json.loads(preflight_path.read_text(encoding="utf-8"))
    if preflight_data.get("status") != "pass":
        print(
            "ERROR: preflight did not pass. Run `python -m design.bedrock preflight` first.",
            file=sys.stderr,
        )
        return 1

    from design.cases import CASES

    responses_dir = output_dir / "responses"
    responses_dir.mkdir(parents=True, exist_ok=True)

    client = boto3.client("bedrock-runtime", region_name=region)
    comparisons = []

    for case in CASES:
        prompt = _build_prompt(case.message)
        prompt_sha256 = _sha256_hex(prompt)
        request_ts = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")

        print(f"Running {case.case_id}: {case.message[:60]}...")
        raw_response = run_trial_case(client, model_id, prompt, max_tokens, temperature)

        # Extract non-secret metadata
        usage = raw_response.get("usage", {})
        metadata = {
            "model_id": model_id,
            "region": region,
            "boto3_version": boto3.__version__,
            "prompt_sha256": prompt_sha256,
            "request_timestamp_utc": request_ts,
            "response_latency_ms": raw_response.get("_latency_ms", 0),
            "input_tokens": usage.get("inputTokens"),
            "output_tokens": usage.get("outputTokens"),
            "stop_reason": raw_response.get("stopReason"),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Strip internal tracking key before saving
        save_response = {k: v for k, v in raw_response.items() if k != "_latency_ms"}

        raw_file = responses_dir / f"{case.case_id}_raw.json"
        raw_file.write_text(
            json.dumps(
                {
                    "case_id": case.case_id,
                    "message": case.message,
                    "raw_response": save_response,
                    "metadata": metadata,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        response_text = _extract_response_text(raw_response)
        parsed, _validation_errors = validate_extraction_output(response_text)
        comparison = compare_case(case, parsed)
        comparison["response_text"] = response_text
        comparisons.append(comparison)
        print(f"  -> {comparison['overall'].upper()}")

    _write_trial_summary(output_dir, comparisons, model_id, region, temperature, max_tokens)
    all_pass = all(c["overall"] == "pass" for c in comparisons)
    pass_count = sum(1 for c in comparisons if c["overall"] == "pass")
    print(f"\nTrial complete: {pass_count}/{len(comparisons)} cases passed.")
    return 0 if all_pass else 1


def cmd_report(args: Any) -> int:
    """Handle: python -m design.bedrock report.

    Regenerate summary from saved responses without API calls.
    """
    output_dir = pathlib.Path(args.output_dir)
    responses_dir = output_dir / "responses"

    from design.cases import CASES

    comparisons = []
    model_id = ""
    region = ""
    temperature = 0.0
    max_tokens = 512

    for case in CASES:
        raw_file = responses_dir / f"{case.case_id}_raw.json"
        if not raw_file.exists():
            print(f"WARNING: {raw_file} not found; skipping {case.case_id}", file=sys.stderr)
            continue

        saved = json.loads(raw_file.read_text(encoding="utf-8"))
        meta = saved.get("metadata", {})
        if not model_id:
            model_id = meta.get("model_id", "unknown")
            region = meta.get("region", "unknown")
            temperature = meta.get("temperature", 0.0)
            max_tokens = meta.get("max_tokens", 512)

        response_text = _extract_response_text(saved.get("raw_response", {}))
        parsed, _ = validate_extraction_output(response_text)
        comparison = compare_case(case, parsed)
        comparison["response_text"] = response_text
        comparisons.append(comparison)

    if not comparisons:
        print(
            "ERROR: no saved raw responses found. Run `python -m design.bedrock trial` first.",
            file=sys.stderr,
        )
        return 1

    _write_trial_summary(output_dir, comparisons, model_id, region, temperature, max_tokens)
    print(f"Report written to {output_dir / 'trial_summary.md'}")
    return 0


def _write_trial_summary(
    output_dir: pathlib.Path,
    comparisons: list[dict[str, Any]],
    model_id: str,
    region: str,
    temperature: float,
    max_tokens: int,
) -> None:
    """Write the trial summary Markdown without any API calls."""
    pass_count = sum(1 for c in comparisons if c["overall"] == "pass")
    total = len(comparisons)

    lines = [
        "# Bedrock Extraction Trial Summary",
        "",
        "## Configuration",
        f"- **Model:** `{model_id}`",
        f"- **Region:** `{region}`",
        f"- **Temperature:** `{temperature}`",
        f"- **Max tokens:** `{max_tokens}`",
        f"- **Overall pass rate:** {pass_count}/{total}",
        "",
        "## Results",
        "",
        "| Case | Message | Result | Notes |",
        "|------|---------|--------|-------|",
    ]

    for c in comparisons:
        msg = c.get("response_text", "")[:80].replace("|", "\\|")
        result = "PASS" if c["overall"] == "pass" else "FAIL"
        notes = "; ".join(c.get("validation_errors", []))[:80] or "-"
        lines.append(f"| {c['case_id']} | {msg} | {result} | {notes} |")

    lines += [
        "",
        "## Field-Level Comparisons",
        "",
    ]

    for c in comparisons:
        lines.append(f"### {c['case_id']} — {c['overall'].upper()}")
        if c.get("validation_errors"):
            lines.append(f"**Validation errors:** {', '.join(c['validation_errors'])}")
        field_results = c.get("field_results", [])
        if field_results:
            lines += [
                "",
                "| Field | Expected | Actual | Match |",
                "|-------|----------|--------|-------|",
            ]
            for fr in field_results:
                match_icon = "Y" if fr["match"] else "N"
                lines.append(
                    f"| {fr['field']} | `{fr['expected']}` | `{fr['actual']}` | {match_icon} |"
                )
        lines.append("")

    lines += [
        "---",
        "_This report was generated from saved raw responses and is reproducible without live AWS calls._",
        "",
    ]

    summary_path = output_dir / "trial_summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
