"""Tests for scripts/gen_summary.py."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCRIPT = REPO_ROOT / "scripts" / "gen_summary.py"
OUTPUT = REPO_ROOT / "docs" / "codebase_summary.md"


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
    """docs/codebase_summary.md is created by the script."""
    subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    assert OUTPUT.exists(), "docs/codebase_summary.md does not exist"


def test_module_table_heading_present():
    """The module table heading '| Module' is present in the output."""
    subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    content = OUTPUT.read_text(encoding="utf-8")
    assert "| Module" in content, "Module table heading not found"


def test_required_section_headings():
    """Sections for walker, resolver, cli, and formats are present."""
    subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    content = OUTPUT.read_text(encoding="utf-8")
    for heading in ("## walker", "## resolver", "## cli", "## formats"):
        assert heading in content, f"Required heading '{heading}' not found"
