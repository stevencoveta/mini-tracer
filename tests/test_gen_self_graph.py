"""Tests for scripts/gen_self_graph.py."""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCRIPT = REPO_ROOT / "scripts" / "gen_self_graph.py"
OUTPUT = REPO_ROOT / "docs" / "self_graph.json"

# Module names produced by the CLI when run against src/mini_tracer/
_MINI_TRACER_MODULES = {"cli", "walker", "resolver", "formats"}


def test_exit_code_zero():
    """Script exits with code 0."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_output_file_exists():
    """docs/self_graph.json is created by the script."""
    subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    assert OUTPUT.exists(), "docs/self_graph.json does not exist"


def test_output_is_valid_json():
    """docs/self_graph.json contains valid JSON."""
    subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    content = OUTPUT.read_text(encoding="utf-8")
    data = json.loads(content)
    assert isinstance(data, dict), "Top-level JSON value is not a dict"


def test_output_has_at_least_one_key():
    """Parsed JSON dict has at least one entry."""
    subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    content = OUTPUT.read_text(encoding="utf-8")
    data = json.loads(content)
    assert len(data) >= 1, "self_graph.json dict is empty"


def test_at_least_one_mini_tracer_key():
    """At least one key in the graph belongs to a mini_tracer module."""
    subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    content = OUTPUT.read_text(encoding="utf-8")
    data = json.loads(content)
    # Keys are like "cli._build_graph", "walker.walk_file", etc.
    # Accept keys that start with a known mini_tracer module name OR contain "mini_tracer".
    matches = [
        k
        for k in data
        if "mini_tracer" in k or k.split(".")[0] in _MINI_TRACER_MODULES
    ]
    assert matches, (
        "No key belonging to a mini_tracer module found in self_graph.json"
    )
