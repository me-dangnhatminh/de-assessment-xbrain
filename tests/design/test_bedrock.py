"""Tests for design.bedrock with mocked boto3 calls."""

from __future__ import annotations

import json
import pathlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from design.bedrock import (
    cmd_report,
    cmd_trial,
    run_preflight,
    run_trial_case,
    validate_extraction_output,
)
from design.cases import CASES

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_converse_response(text: str) -> dict:
    """Build a minimal Converse API response dict containing *text*."""
    return {
        "output": {"message": {"content": [{"text": text}]}},
        "stopReason": "end_turn",
        "usage": {"inputTokens": 20, "outputTokens": 50, "totalTokens": 70},
        "metrics": {"latencyMs": 123},
        "_latency_ms": 123,
    }


VALID_EXTRACTION = json.dumps(
    {
        "event_type": "CONNECTION_TIMEOUT",
        "component": "db-primary",
        "parameters": {"retry": "3"},
        "confidence": "high",
        "parse_status": "success",
    }
)


# ---------------------------------------------------------------------------
# Preflight tests
# ---------------------------------------------------------------------------


def test_preflight_missing_region_env_var() -> None:
    result = run_preflight("", "some-model")
    assert result["status"] == "fail"
    assert "region" in result["check"]


@patch("boto3.client")
def test_preflight_access_denied(mock_boto3_client) -> None:
    import botocore.exceptions

    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client
    mock_client.converse.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "converse"
    )
    result = run_preflight("us-east-1", "some-model")
    assert result["status"] == "fail"
    assert "AccessDeniedException" in result["error_code"]


@patch("boto3.client")
def test_preflight_model_not_found(mock_boto3_client) -> None:
    import botocore.exceptions

    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client
    mock_client.converse.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": "Model not found"}}, "converse"
    )
    result = run_preflight("us-east-1", "bad-model-id")
    assert result["status"] == "fail"


@patch("boto3.client")
def test_preflight_converse_not_supported(mock_boto3_client) -> None:
    import botocore.exceptions

    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client
    mock_client.converse.side_effect = botocore.exceptions.ClientError(
        {
            "Error": {
                "Code": "ValidationException",
                "Message": "The model does not support Converse API",
            }
        },
        "converse",
    )
    result = run_preflight("us-east-1", "unsupported-model")
    assert result["status"] == "fail"
    assert "converse" in result["check"]


@patch("boto3.client")
def test_preflight_success(mock_boto3_client) -> None:
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client
    mock_client.converse.return_value = make_mock_converse_response("pong")

    result = run_preflight("us-east-1", "anthropic.claude-3-haiku-20240307-v1:0")
    assert result["status"] == "pass"
    assert "boto3_version" in result


# ---------------------------------------------------------------------------
# Trial runner tests
# ---------------------------------------------------------------------------


def test_trial_refuses_without_passing_preflight(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")
    args = SimpleNamespace(output_dir=str(tmp_path))
    rc = cmd_trial(args)
    assert rc == 1


@patch("boto3.client")
def test_trial_saves_raw_response(mock_boto3_client, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")

    # Write passing preflight result
    preflight = {"status": "pass", "model_id": "test-model", "region": "us-east-1"}
    (tmp_path / "preflight_result.json").write_text(json.dumps(preflight))

    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client
    mock_client.converse.return_value = make_mock_converse_response(VALID_EXTRACTION)

    args = SimpleNamespace(output_dir=str(tmp_path))
    cmd_trial(args)

    assert (tmp_path / "responses" / "tc01_raw.json").exists()


@patch("boto3.client")
def test_trial_validates_schema(mock_boto3_client, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")

    preflight = {"status": "pass", "model_id": "test-model", "region": "us-east-1"}
    (tmp_path / "preflight_result.json").write_text(json.dumps(preflight))

    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client
    mock_client.converse.return_value = make_mock_converse_response(VALID_EXTRACTION)

    args = SimpleNamespace(output_dir=str(tmp_path))
    cmd_trial(args)

    raw = json.loads((tmp_path / "responses" / "tc01_raw.json").read_text())
    assert raw["case_id"] == "tc01"
    assert "metadata" in raw


def test_trial_handles_invalid_json_output() -> None:
    parsed, errors = validate_extraction_output("not valid json")
    assert parsed is None
    assert errors == ["output is not valid JSON"]


@patch("boto3.client")
def test_trial_records_metadata(mock_boto3_client) -> None:
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client
    mock_response = make_mock_converse_response(VALID_EXTRACTION)
    mock_client.converse.return_value = mock_response

    response = run_trial_case(mock_client, "test-model", "test prompt", 512, 0.0)
    assert response["usage"]["inputTokens"] == 20


# ---------------------------------------------------------------------------
# Report generator tests
# ---------------------------------------------------------------------------


def _write_fake_response(responses_dir: pathlib.Path, case_id: str) -> None:
    """Write a fake raw response file for testing report determinism."""
    data = {
        "case_id": case_id,
        "message": "ERR ConnTimeout db-primary after 30s retry=3",
        "raw_response": make_mock_converse_response(VALID_EXTRACTION),
        "metadata": {
            "model_id": "test-model",
            "region": "us-east-1",
            "boto3_version": "1.43.68",
            "prompt_sha256": "abc123",
            "request_timestamp_utc": "2026-08-12T00:00:00Z",
            "response_latency_ms": 100,
            "input_tokens": 20,
            "output_tokens": 50,
            "stop_reason": "end_turn",
            "temperature": 0.0,
            "max_tokens": 512,
        },
    }
    (responses_dir / f"{case_id}_raw.json").write_text(json.dumps(data, indent=2))


def test_report_is_deterministic(tmp_path) -> None:
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    for case in CASES:
        _write_fake_response(responses_dir, case.case_id)

    args = SimpleNamespace(output_dir=str(tmp_path))
    cmd_report(args)
    first = (tmp_path / "trial_summary.md").read_text()

    cmd_report(args)
    second = (tmp_path / "trial_summary.md").read_text()

    assert first == second


@patch("boto3.client")
def test_report_without_api_calls(mock_boto3, tmp_path) -> None:
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    for case in CASES:
        _write_fake_response(responses_dir, case.case_id)

    args = SimpleNamespace(output_dir=str(tmp_path))
    cmd_report(args)

    mock_boto3.assert_not_called()
