.PHONY: all test lint install check help

help:
	@echo "mini-tracer — development helpers"
	@echo ""
	@echo "  make test     - run pytest (assert + lint gate)"
	@echo "  make lint     - run ruff check"
	@echo "  make check    - full check: test + lint"
	@echo "  make install  - uv sync --extra dev (one-off setup)"

install:
	uv sync --extra dev

test:
	uv run pytest

lint:
	uv run ruff check src/ tests/

check: lint test

all: check
