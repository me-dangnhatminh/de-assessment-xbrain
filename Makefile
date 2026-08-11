UV ?= uv
INPUT := docs/onboard/datapack/data/app_logs_7days.jsonl
OUTPUT_ROOT := data
DOCS_DIR := docs/onboard/datapack/data/docs
KB_OUTPUT_DIR := data/evidence/phase2
# Canonical command form: uv run --locked python -m pipeline <stage>.

ifeq ($(shell command -v $(UV) >/dev/null 2>&1; echo $$?),0)
PYTHON := $(UV) run --locked python
RUN := $(PYTHON) -m pipeline
RUFF := $(UV) run --locked ruff
PYTEST := $(UV) run --locked pytest
SYNC := $(UV) sync --locked
LOCK_CHECK := $(UV) lock --check
else
PYTHON := .venv/bin/python
RUN := $(PYTHON) -m pipeline
RUFF := $(PYTHON) -m ruff
PYTEST := $(PYTHON) -m pytest
SYNC := @test -x .venv/bin/python && echo "uv is unavailable; using the existing locked .venv fallback"
LOCK_CHECK := @test -f uv.lock && echo "uv is unavailable; checked-in uv.lock present"
endif

.PHONY: sync integrity pipeline analysis report verify-phase1 phase1 clean-checkout-verify kb-build kb-search

sync:
	$(SYNC)

integrity:
	$(RUN) integrity --input $(INPUT) --output-root $(OUTPUT_ROOT)

pipeline:
	$(RUN) run --input $(INPUT) --output-root $(OUTPUT_ROOT)

analysis:
	$(RUN) analyze --input $(INPUT) --output-root $(OUTPUT_ROOT)

report:
	$(RUN) report --input $(INPUT) --output-root $(OUTPUT_ROOT)

verify-phase1: phase1
	$(LOCK_CHECK)
	$(RUFF) check .
	$(RUFF) format --check --exclude .planning .
	$(PYTEST) -q
	git diff --exit-code -- docs/onboard

phase1: sync
	$(RUN) all --input $(INPUT) --output-root $(OUTPUT_ROOT)

# Optional: simulate a fresh machine in Docker (no .venv, no uv cache) and
# prove `uv sync --locked` plus the documented trace command work. Requires
# docker; the pipeline itself does not depend on it.
clean-checkout-verify:
	bash scripts/verify-clean-checkout.sh

# ---------------------------------------------------------------------------
# Phase 2: Version-aware knowledge base
# ---------------------------------------------------------------------------

kb-build: sync
	$(PYTHON) -m kb build --docs-dir $(DOCS_DIR) --output-dir $(KB_OUTPUT_DIR)

kb-search: $(KB_OUTPUT_DIR)/index.sqlite
	$(PYTHON) -m kb search --db $(KB_OUTPUT_DIR)/index.sqlite --query "sao lưu" --mode current
	@echo "---"
	$(PYTHON) -m kb search --db $(KB_OUTPUT_DIR)/index.sqlite --query "sao lưu" --mode all

$(KB_OUTPUT_DIR)/index.sqlite: kb-build
