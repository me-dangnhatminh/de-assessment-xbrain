# Clean-machine simulation for Phase 1 truth #6: a fresh container with uv
# installed and a pristine committed checkout (no .venv, no uv cache, no
# ambient packages) must run `uv sync --locked` and the documented trace
# command without the Makefile fallback.
#
# This is an optional, local-only verification harness. Docker is NOT a
# pipeline runtime dependency; the pipeline itself runs on CPython + uv.
FROM python:3.12-slim

# uv is a standalone binary; the PyPI wheel avoids apt/curl in the slim image.
RUN pip install --no-cache-dir --break-system-packages uv

# The build context is `scripts/verify-clean-checkout.sh` output: the committed
# tree extracted from `git archive HEAD` under a `context/` directory.
COPY context /work/xbrain
WORKDIR /work/xbrain

# Refuse to simulate a "clean" machine if a virtualenv leaked into the copy.
RUN test ! -e .venv && echo "fresh copy has no .venv"
