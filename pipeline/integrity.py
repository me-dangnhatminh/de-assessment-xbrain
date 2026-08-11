"""Source-integrity controls for immutable assessment inputs and generated outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SUPPLIED_ROOT = REPOSITORY_ROOT / "docs/onboard"
CANONICAL_LOG_INPUT = SUPPLIED_ROOT / "datapack/data/app_logs_7days.jsonl"


class SourceIntegrityError(ValueError):
    """Raised when a generated path could affect supplied source material."""


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one file without changing its bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_canonical_log_input(input_path: Path) -> Path:
    """Resolve and authorize the only supplied JSONL allowed for production evidence."""
    resolved_input = input_path.expanduser().resolve()
    canonical_input = CANONICAL_LOG_INPUT.resolve()
    if resolved_input != canonical_input:
        raise SourceIntegrityError(
            "production input must be the canonical supplied log: "
            "docs/onboard/datapack/data/app_logs_7days.jsonl"
        )
    return canonical_input


def inventory_supplied_inputs(supplied_root: Path = SUPPLIED_ROOT) -> list[dict[str, str]]:
    """Hash every regular supplied file in stable, repository-independent order."""
    resolved_root = supplied_root.expanduser().resolve()
    if not resolved_root.is_dir():
        raise SourceIntegrityError(f"supplied input root does not exist: {resolved_root}")
    files = sorted(path for path in resolved_root.rglob("*") if path.is_file())
    return [
        {"path": path.relative_to(resolved_root).as_posix(), "sha256": sha256_file(path)}
        for path in files
    ]


def assert_source_unchanged(before: list[dict[str, str]], after: list[dict[str, str]]) -> None:
    """Fail closed when supplied-file membership or bytes differ across a run."""
    if before != after:
        raise SourceIntegrityError("supplied input inventory changed during pipeline execution")


def validate_output_root(output_root: Path, supplied_root: Path = SUPPLIED_ROOT) -> Path:
    """Resolve an output root and reject any alias inside the immutable supplied tree."""
    resolved_output = output_root.expanduser().resolve()
    resolved_supplied = supplied_root.expanduser().resolve()
    try:
        resolved_output.relative_to(resolved_supplied)
    except ValueError:
        return resolved_output
    raise SourceIntegrityError(
        f"output root must be outside immutable supplied inputs: {resolved_supplied}"
    )
