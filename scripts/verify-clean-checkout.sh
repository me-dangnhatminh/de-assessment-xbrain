#!/usr/bin/env bash
# Verify Phase 1 truth #6 in a Docker-simulated clean machine.
#
# Builds a fresh container from the committed tree (via `git archive HEAD`, so
# no .venv, uv cache, or ambient packages leak in), installs uv, and requires
# `uv sync --locked`, `uv lock --check`, and the documented trace command to
# succeed with all four trace artifacts written.
#
# This is an optional local harness; the pipeline itself does not depend on
# Docker. Requires: docker, git, GNU tar. Run from the repository root, or via
# `make clean-checkout-verify`.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image="xbrain-clean-checkout"

if ! command -v docker >/dev/null 2>&1; then
    echo "error: docker is required for make clean-checkout-verify" >&2
    exit 1
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/context"

# The committed tree only: exactly what a fresh `git clone` would contain.
git -C "$repo" archive --format=tar HEAD | tar -x -C "$work/context"
if [ -e "$work/context/.venv" ]; then
    echo "error: committed tree unexpectedly contains .venv" >&2
    exit 1
fi

docker build -q -f "$repo/scripts/docker/clean-checkout.Dockerfile" -t "$image" "$work" >/dev/null
docker run --rm "$image" bash -euo pipefail -c '
    echo "== uv =="
    uv --version
    echo "== python =="
    python --version
    echo "== .venv present? =="
    test ! -e .venv && echo "no"
    echo "== uv sync --locked =="
    uv sync --locked
    echo "== uv lock --check =="
    uv lock --check
    echo "== documented trace command =="
    uv run --locked python -m pipeline trace --output-root /tmp/trace
    test -f /tmp/trace/quality_ledger.jsonl
    test -f /tmp/trace/trace.parquet
    test -f /tmp/trace/trace_manifest.json
    test -f /tmp/trace/tables/00_tracer_service_error_counts.csv
    echo "clean-checkout verification passed"
'
