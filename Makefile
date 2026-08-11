UV ?= uv
INPUT := docs/onboard/datapack/data/app_logs_7days.jsonl
OUTPUT_ROOT := data
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

.PHONY: sync integrity pipeline analysis report verify-phase1 phase1

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
