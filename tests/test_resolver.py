"""Tests for the resolver module."""

import os
import tempfile
import textwrap
from pathlib import Path

from mini_tracer.resolver import _build_import_table, resolve, walk_dir

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
        file_graphs = {tmp_path: {"main": ["helper"]}}
        result = resolve(file_graphs)
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


def test_resolve_plain_import():
    """'import os' makes bare 'os' calls resolve to 'os' (identity)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(textwrap.dedent("""\
            import os

            def read():
                os()
        """))
        tmp_path = fh.name

    try:
        # os is in the import table; bare 'os' should map to 'os' (identity).
        file_graphs = {tmp_path: {"read": ["os"]}}
        result = resolve(file_graphs)
        assert result["read"] == ["os"]
    finally:
        os.unlink(tmp_path)


def test_resolve_plain_import_with_alias():
    """'import os as operating_system' maps 'operating_system' to 'os'."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(textwrap.dedent("""\
            import os as operating_system

            def run():
                operating_system()
        """))
        tmp_path = fh.name

    try:
        file_graphs = {tmp_path: {"run": ["operating_system"]}}
        result = resolve(file_graphs)
        assert result["run"] == ["os"]
    finally:
        os.unlink(tmp_path)


def test_resolve_duplicate_callees_preserved():
    """If a function calls the same name twice, both entries are kept."""
    file_graphs = {
        "dup.py": {
            "repeat": ["helper", "helper"],
        }
    }
    result = resolve(file_graphs)
    assert result["repeat"] == ["helper", "helper"]


def test_resolve_empty_callee_list():
    """A function that makes no calls produces an empty callee list."""
    file_graphs = {
        "leaf.py": {
            "leaf_func": [],
        }
    }
    result = resolve(file_graphs)
    assert result["leaf_func"] == []


# ---------------------------------------------------------------------------
# _build_import_table() tests
# ---------------------------------------------------------------------------


def test_build_import_table_from_import():
    """'from mod import func' produces {'func': 'mod.func'}."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write("from mod import func\n")
        tmp_path = fh.name

    try:
        table = _build_import_table(tmp_path)
        assert table == {"func": "mod.func"}
    finally:
        os.unlink(tmp_path)


def test_build_import_table_plain_import():
    """'import os' produces {'os': 'os'}."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write("import os\n")
        tmp_path = fh.name

    try:
        table = _build_import_table(tmp_path)
        assert table["os"] == "os"
    finally:
        os.unlink(tmp_path)


def test_build_import_table_alias():
    """'from mod import func as f' produces {'f': 'mod.func'}."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write("from mod import func as f\n")
        tmp_path = fh.name

    try:
        table = _build_import_table(tmp_path)
        assert table == {"f": "mod.func"}
    finally:
        os.unlink(tmp_path)


def test_build_import_table_star_import_skipped():
    """'from mod import *' is skipped; table remains empty."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write("from mod import *\n")
        tmp_path = fh.name

    try:
        table = _build_import_table(tmp_path)
        assert table == {}
    finally:
        os.unlink(tmp_path)


def test_build_import_table_missing_file():
    """A nonexistent path returns an empty table without raising."""
    table = _build_import_table("/nonexistent/path/does_not_exist.py")
    assert table == {}


def test_build_import_table_syntax_error():
    """A file with a syntax error returns an empty table without raising."""
    table = _build_import_table("tests/fixtures/syntax_error.py")
    assert table == {}


def test_build_import_table_multiple_imports():
    """Multiple from-imports all appear in the table."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(textwrap.dedent("""\
            from mod_a import alpha
            from mod_b import beta, gamma
            import delta
        """))
        tmp_path = fh.name

    try:
        table = _build_import_table(tmp_path)
        assert table["alpha"] == "mod_a.alpha"
        assert table["beta"] == "mod_b.beta"
        assert table["gamma"] == "mod_b.gamma"
        assert table["delta"] == "delta"
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# walk_dir() tests
# ---------------------------------------------------------------------------


def test_walk_dir_fixture():
    """walk_dir over the fixtures directory returns a non-empty graph."""
    result = walk_dir("tests/fixtures")
    assert len(result) > 0
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


def test_walk_dir_skips_syntax_error_file():
    """walk_dir silently skips files with syntax errors and processes others."""
    with tempfile.TemporaryDirectory() as tmpdir:
        good = os.path.join(tmpdir, "good.py")
        bad = os.path.join(tmpdir, "bad.py")

        with open(good, "w", encoding="utf-8") as fh:
            fh.write(textwrap.dedent("""\
                def good_func():
                    helper()
            """))
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("def broken(\n    # intentional syntax error\n")

        result = walk_dir(tmpdir)
        # good.py's function must appear; bad.py must not cause a crash.
        assert "good_func" in result


def test_walk_dir_class_methods_qualified():
    """walk_dir over the classes fixture contains class-qualified method names."""
    result = walk_dir("tests/fixtures")
    assert "MyClass.method_a" in result
    assert "MyClass.method_b" in result


def test_walk_dir_multiple_files_merged():
    """walk_dir merges graphs from multiple .py files into one dict."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_a = os.path.join(tmpdir, "a.py")
        file_b = os.path.join(tmpdir, "b.py")

        with open(file_a, "w", encoding="utf-8") as fh:
            fh.write("def alpha():\n    pass\n")
        with open(file_b, "w", encoding="utf-8") as fh:
            fh.write("def beta():\n    pass\n")

        result = walk_dir(tmpdir)
        assert "alpha" in result
        assert "beta" in result
