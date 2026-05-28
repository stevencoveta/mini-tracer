#!/usr/bin/env bash
set -e

uv run python scripts/gen_summary.py
uv run python scripts/gen_self_graph.py
