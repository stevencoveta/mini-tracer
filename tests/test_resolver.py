"""Tests for the resolver module."""

import os
import tempfile
import textwrap
from pathlib import Path

from mini_tracer.resolver import resolve, walk_dir

# ---------------------------------------------------------------------------
# resolve() tests
# ---------------------------------------------------------------------------


def test_resolve_single_file_passthrough():
    """Single-file graph with no imports passes through unchanged."""
    file_graphs = {
        "a.py": {
            "foo": ["bar", "baz"],
            "bar": ["baz"],
            "baz": [],
        }
    }
    result = resolve(file_graphs)
    assert result["foo"] == ["bar", "baz"]
    assert result["bar"] == ["baz"]
    assert result["baz"] == []


def test_resolve_cross_module_edge():
    """Bare 'helper' call resolves to 'utils.helper' via from-import."""
    # Write a temporary file that imports from another module.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(textwrap.dedent("""\
            from utils import helper

            def main():
                helper()
        """))
        tmp_path = fh.name

    try:
        # Simulate the graph that walk_file would produce for this file.
        file_graphs = {tmp_path: {"main": ["helper"]}}
        result = resolve(file_graphs)
        # 'helper' should now be resolved to 'utils.helper'.
        assert result["main"] == ["utils.helper"]
    finally:
        os.unlink(tmp_path)


def test_resolve_unresolvable_callee_kept_verbatim():
    """A callee not found in any import table is kept as-is."""
    file_graphs = {
        "b.py": {
            "do_work": ["mystery_func", "another_unknown"],
        }
    }
    result = resolve(file_graphs)
    assert result["do_work"] == ["mystery_func", "another_unknown"]


def test_resolve_already_qualified_names_unchanged():
    """Callees that already contain a dot are left alone."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write("from utils import helper\n\ndef go():\n    pass\n")
        tmp_path = fh.name

    try:
        file_graphs = {tmp_path: {"go": ["utils.helper"]}}
        result = resolve(file_graphs)
        # Already qualified — must not be double-qualified.
        assert result["go"] == ["utils.helper"]
    finally:
        os.unlink(tmp_path)


def test_resolve_empty_graph():
    """Resolving an empty file_graphs dict returns an empty dict."""
    assert resolve({}) == {}


def test_resolve_import_alias():
    """'from utils import helper as h' makes 'h' resolve to 'utils.helper'."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(textwrap.dedent("""\
            from utils import helper as h

            def run():
                h()
        """))
        tmp_path = fh.name

    try:
        file_graphs = {tmp_path: {"run": ["h"]}}
        result = resolve(file_graphs)
        assert result["run"] == ["utils.helper"]
    finally:
        os.unlink(tmp_path)


def test_resolve_multiple_files_merged():
    """Graphs from multiple files are all present in the merged result."""
    file_graphs = {
        "mod_a.py": {"alpha": ["beta"]},
        "mod_b.py": {"beta": ["gamma"], "gamma": []},
    }
    result = resolve(file_graphs)
    assert "alpha" in result
    assert "beta" in result
    assert "gamma" in result


# ---------------------------------------------------------------------------
# walk_dir() tests
# ---------------------------------------------------------------------------


def test_walk_dir_fixture():
    """walk_dir over the fixtures directory returns a non-empty graph."""
    result = walk_dir("tests/fixtures")
    # fixtures contain multiple functions; result must be non-empty.
    assert len(result) > 0
    # Functions from simple.py should appear.
    assert "foo" in result
    assert "bar" in result
    assert "baz" in result


def test_walk_dir_resolves_imports():
    """walk_dir resolves from-imports to qualified names end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        caller = os.path.join(tmpdir, "caller.py")
        with open(caller, "w", encoding="utf-8") as fh:
            fh.write(textwrap.dedent("""\
                from utils import helper

                def main():
                    helper()
            """))

        result = walk_dir(tmpdir)
        assert "main" in result
        assert result["main"] == ["utils.helper"]


def test_walk_dir_empty_directory():
    """walk_dir on a directory with no .py files returns an empty graph."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = walk_dir(tmpdir)
        assert result == {}


def test_walk_dir_accepts_path_object():
    """walk_dir accepts a pathlib.Path as well as a string."""
    result = walk_dir(Path("tests/fixtures"))
    assert isinstance(result, dict)
    assert len(result) > 0
