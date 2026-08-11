"""Bounded, provenance-first physical-line ingestion for immutable JSONL inputs."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pipeline.models import Disposition, Issue, SourceEnvelope

DEFAULT_MAX_LINE_BYTES = 1_048_576


def _issue(
    issue_code: str,
    reason: str,
    *,
    original_value: Any = None,
    field: str | None = None,
) -> Issue:
    return Issue(
        issue_code=issue_code,
        field=field,
        original_value=original_value,
        normalized_value=None,
        action=Disposition.REJECT,
        reason=reason,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def iter_source_lines(
    input_path: Path, max_line_bytes: int = DEFAULT_MAX_LINE_BYTES
) -> Iterator[SourceEnvelope]:
    """Yield every physical line with provenance before decoding or JSON parsing."""
    if max_line_bytes < 1:
        raise ValueError("max_line_bytes must be a positive integer")

    resolved_path = input_path.expanduser().resolve()
    source_sha256 = _sha256_file(resolved_path)
    with resolved_path.open("rb") as source:
        for source_line, raw_bytes in enumerate(source, start=1):
            preparse_issues: tuple[Issue, ...] = ()
            if len(raw_bytes) > max_line_bytes:
                raw_line = raw_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
                preparse_issues = (
                    _issue(
                        "LINE_TOO_LARGE",
                        f"physical line exceeds the {max_line_bytes}-byte parsing limit",
                        original_value=len(raw_bytes),
                    ),
                )
            else:
                try:
                    raw_line = raw_bytes.decode("utf-8").rstrip("\r\n")
                except UnicodeDecodeError:
                    # Byte-safe rejected-row representation: the envelope keeps a
                    # lossy string for provenance, but strict decoding already
                    # proved the bytes are not valid UTF-8.
                    raw_line = raw_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
                    preparse_issues = (
                        _issue(
                            "TEXT_INVALID_UTF8",
                            "physical line is not valid UTF-8 and cannot be parsed as JSON text",
                        ),
                    )
            yield SourceEnvelope(
                source_path=str(resolved_path),
                source_sha256=source_sha256,
                source_line=source_line,
                raw_line=raw_line,
                preparse_issues=preparse_issues,
            )


def _reject_json_constant(value: str) -> None:
    """Reject NaN/Infinity/-Infinity instead of silently accepting non-standard JSON."""
    raise ValueError(f"non-standard JSON constant is not accepted: {value}")


def parse_json_line(envelope: SourceEnvelope) -> tuple[dict[str, Any] | None, tuple[Issue, ...]]:
    """Parse one envelope without losing pre-parse failures or source provenance."""
    if envelope.preparse_issues:
        return None, envelope.preparse_issues
    try:
        parsed = json.loads(envelope.raw_line, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError):
        return None, (
            _issue(
                "JSON_MALFORMED",
                "physical line is not valid JSON",
                original_value=envelope.raw_line,
            ),
        )
    if not isinstance(parsed, dict):
        return None, (
            _issue(
                "JSON_NOT_OBJECT",
                "JSON value must be an object representing one log record",
                original_value=parsed,
            ),
        )
    return parsed, ()


def canonical_record_digest(record: dict[str, Any]) -> str:
    """Hash the complete parsed object, independent of JSON key order or spacing."""
    canonical = json.dumps(
        record, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
