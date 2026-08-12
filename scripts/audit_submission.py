"""Submission audit script — verifies the repository is reviewer-ready.

Checks:
1. Required deliverables exist
2. Tests pass and lint is clean
3. Source integrity (docs/onboard/ unchanged)
4. No secrets or absolute machine paths in committed files
5. Page-limit compliance for bounded documents
6. .gitignore covers caches and .env

Usage:
    python scripts/audit_submission.py [--skip-tests] [--skip-regen]
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

# Word count per page approximation (generous — allows up to 700 words per page)
WORDS_PER_PAGE = 700

# Documents with page limits: (path, max_pages)
PAGE_LIMITED_DOCS = [
    ("design/aws_daily_pipeline.md", 1),
    ("design/ai_response_review.md", 1),
    ("design/extraction_prompt.md", 2),
]

REQUIRED_DELIVERABLES = [
    "README.md",
    "AI_WORKLOG.md",
    "Makefile",
    "run_manifest.json",
    "pipeline/__init__.py",
    "pipeline/__main__.py",
    "kb/__init__.py",
    "kb/__main__.py",
    "design/__main__.py",
    "design/aws_daily_pipeline.md",
    "design/aws_daily_pipeline.png",
    "design/ai_response_review.md",
    "design/extraction_prompt.md",
    "design/output/preflight_result.json",
    "design/output/trial_summary.md",
    "sop/kb_update_sop.md",
    "data/evidence/phase1/run_manifest.json",
    "data/evidence/phase1/quality_ledger.jsonl",
    "data/processed/logs_clean.parquet",
    "data/evidence/phase2/chunks.jsonl",
    "data/evidence/phase2/eval_results.json",
    "data/evidence/phase2/index.sqlite",
]

# Patterns that indicate leaked secrets or machine-specific state
SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", "possible secret key (40 hex)"),
    (r"/mnt/data/Minh", "absolute machine path leak"),
    (r"/home/dangnhatminh", "absolute home path leak"),
]

# Paths to exclude from secret scanning (binary, lock files, planning, caches)
SCAN_EXCLUDE_DIRS = {
    ".venv",
    ".git",
    "__pycache__",
    ".planning",
    "node_modules",
    ".tmp",
    ".ruff_cache",
    ".pytest_cache",
}
# This script itself is excluded — it contains the patterns as literals for matching
SCAN_EXCLUDE_FILES = {"scripts/audit_submission.py", "AI_WORKLOG.md"}
SCAN_EXCLUDE_EXTENSIONS = {".sqlite", ".parquet", ".png", ".drawio", ".lock"}


class AuditResult:
    def __init__(self) -> None:
        self.passes: list[str] = []
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def ok(self, msg: str) -> None:
        self.passes.append(msg)

    def fail(self, msg: str) -> None:
        self.failures.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def passed(self) -> bool:
        return len(self.failures) == 0


def check_deliverables(result: AuditResult) -> None:
    """Verify all required deliverable paths exist."""
    missing = []
    for rel_path in REQUIRED_DELIVERABLES:
        if not (REPOSITORY_ROOT / rel_path).exists():
            missing.append(rel_path)
    if missing:
        result.fail(f"Missing deliverables: {', '.join(missing)}")
    else:
        result.ok(f"All {len(REQUIRED_DELIVERABLES)} required deliverables present")


def check_page_limits(result: AuditResult) -> None:
    """Verify page-limited documents are within bounds."""
    for rel_path, max_pages in PAGE_LIMITED_DOCS:
        full_path = REPOSITORY_ROOT / rel_path
        if not full_path.is_file():
            result.warn(f"Page-limit check skipped (missing): {rel_path}")
            continue
        text = full_path.read_text(encoding="utf-8")
        word_count = len(text.split())
        max_words = max_pages * WORDS_PER_PAGE
        if word_count > max_words:
            result.fail(
                f"Page limit exceeded: {rel_path} has {word_count} words "
                f"(limit: {max_words} for {max_pages} page(s))"
            )
        else:
            result.ok(f"Page limit OK: {rel_path} ({word_count}/{max_words} words)")


def check_source_integrity(result: AuditResult) -> None:
    """Verify docs/onboard/ is unchanged from git HEAD."""
    completed = subprocess.run(
        ["git", "diff", "--exit-code", "--", "docs/onboard"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        result.fail("Source integrity: docs/onboard/ has uncommitted changes")
    else:
        result.ok("Source integrity: docs/onboard/ unchanged")


def check_secrets(result: AuditResult) -> None:
    """Scan committed text files for secret/path leaks."""
    issues: list[str] = []
    for path in REPOSITORY_ROOT.rglob("*"):
        if not path.is_file():
            continue
        # Skip excluded dirs and excluded files
        rel = path.relative_to(REPOSITORY_ROOT)
        if any(part in SCAN_EXCLUDE_DIRS for part in rel.parts):
            continue
        if rel.as_posix() in SCAN_EXCLUDE_FILES:
            continue
        if rel.suffix in SCAN_EXCLUDE_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for pattern, label in SECRET_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                issues.append(f"  {rel}: {label} ({len(matches)} match(es))")
    if issues:
        result.fail("Secret/path scan found issues:\n" + "\n".join(issues))
    else:
        result.ok("Secret/path scan: no leaks detected")


def check_gitignore(result: AuditResult) -> None:
    """Verify critical paths are git-ignored."""
    gitignore_path = REPOSITORY_ROOT / ".gitignore"
    if not gitignore_path.is_file():
        result.fail(".gitignore is missing")
        return
    content = gitignore_path.read_text(encoding="utf-8")
    required_patterns = [".venv/", "__pycache__/", ".env", ".pytest_cache/", ".ruff_cache/"]
    missing = [p for p in required_patterns if p not in content]
    if missing:
        result.fail(f".gitignore missing patterns: {', '.join(missing)}")
    else:
        result.ok(".gitignore covers all required exclusions")

    # Verify .env is not tracked
    completed = subprocess.run(
        ["git", "ls-files", ".env"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.stdout.strip():
        result.fail(".env is tracked by git — NEVER commit credentials")
    else:
        result.ok(".env is not tracked")


def check_tests_lint(result: AuditResult, skip: bool = False) -> None:
    """Run pytest and ruff checks."""
    if skip:
        result.warn("Tests/lint skipped (--skip-tests)")
        return

    python = shutil.which("python") or sys.executable

    # pytest
    completed = subprocess.run(
        [python, "-m", "pytest", "-q", "--tb=line"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if completed.returncode != 0:
        result.fail(f"pytest failed:\n{completed.stdout[-500:]}")
    else:
        # Extract pass count
        last_line = completed.stdout.strip().split("\n")[-1]
        result.ok(f"pytest: {last_line}")

    # ruff check
    completed = subprocess.run(
        [python, "-m", "ruff", "check", "."],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        result.fail(f"ruff check failed:\n{completed.stdout[:500]}")
    else:
        result.ok("ruff check: clean")

    # ruff format
    completed = subprocess.run(
        [python, "-m", "ruff", "format", "--check", "--exclude", ".planning", "."],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        result.fail(f"ruff format check failed:\n{completed.stdout[:500]}")
    else:
        result.ok("ruff format: clean")


def check_manifest(result: AuditResult) -> None:
    """Verify root run_manifest.json exists and is valid JSON with run_id."""
    manifest_path = REPOSITORY_ROOT / "run_manifest.json"
    if not manifest_path.is_file():
        result.fail("Root run_manifest.json is missing (run `make manifest`)")
        return
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        result.fail(f"run_manifest.json is invalid JSON: {e}")
        return
    if "run_id" not in data:
        result.fail("run_manifest.json missing run_id")
    else:
        result.ok(f"run_manifest.json valid (run_id: {data['run_id'][:16]}...)")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Audit submission readiness.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest/ruff")
    parser.add_argument("--skip-regen", action="store_true", help="Skip regeneration check")
    args = parser.parse_args()

    result = AuditResult()

    print("=" * 60)
    print("SUBMISSION AUDIT")
    print("=" * 60)

    check_deliverables(result)
    check_page_limits(result)
    check_source_integrity(result)
    check_secrets(result)
    check_gitignore(result)
    check_manifest(result)
    check_tests_lint(result, skip=args.skip_tests)

    print()
    print("-" * 60)
    for msg in result.passes:
        print(f"  ✓ {msg}")
    for msg in result.warnings:
        print(f"  ⚠ {msg}")
    for msg in result.failures:
        print(f"  ✗ {msg}")
    print("-" * 60)

    total = len(result.passes) + len(result.failures) + len(result.warnings)
    print(
        f"\n{'PASSED' if result.passed else 'FAILED'}: "
        f"{len(result.passes)}/{total} checks passed"
        f"{f', {len(result.warnings)} warnings' if result.warnings else ''}"
        f"{f', {len(result.failures)} failures' if result.failures else ''}"
    )

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
