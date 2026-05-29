"""Tests for the walker module."""

import ast
import os
import tempfile
import textwrap

from mini_tracer.walker import _CallCollector, _extract_name, walk_file

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _walk_source(source: str) -> dict[str, list[str]]:
    """Write *source* to a temp file, walk it, and return the graph."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as fh:
        fh.write(textwrap.dedent(source))
        name = fh.name
    try:
        return walk_file(name)
    finally:
        os.unlink(name)


# ---------------------------------------------------------------------------
# Fixture-based tests
# ---------------------------------------------------------------------------

def test_walk_simple_file():
    """Walking simple.py produces the expected call edges."""
    graph = walk_file("tests/fixtures/simple.py")
    assert "foo" in graph
    assert "bar" in graph
    assert "baz" in graph
    assert set(graph["foo"]) == {"bar", "baz"}
    assert graph["bar"] == ["baz"]
    assert graph["baz"] == []


def test_walk_classes():
    """Class methods are keyed as ClassName.method_name."""
    graph = walk_file("tests/fixtures/classes.py")
    assert "MyClass.method_a" in graph
    assert "MyClass.method_b" in graph
    assert "foo" in graph
    assert "bar" in graph
    # self.method_b() inside method_a should appear as "method_b"
    assert "method_b" in graph["MyClass.method_a"]
    # method_b calls top-level foo
    assert "foo" in graph["MyClass.method_b"]


def test_walk_nonexistent():
    """A missing file returns an empty graph (no exception)."""
    graph = walk_file("tests/fixtures/nonexistent.py")
    assert graph == {}


def test_walk_syntax_error_file():
    """A file with a syntax error returns an empty graph (no exception)."""
    graph = walk_file("tests/fixtures/syntax_error.py")
    assert graph == {}


def test_walk_async_functions():
    """Async functions are collected and their call edges are captured."""
    graph = walk_file("tests/fixtures/async_funcs.py")
    assert "fetch" in graph
    assert "process" in graph
    assert "helper" in graph
    assert graph["fetch"] == ["process"]
    assert graph["process"] == ["helper"]
    assert graph["helper"] == []


def test_walk_builtins_filtered():
    """Built-in calls (len, str, range …) must not appear as call edges."""
    graph = walk_file("tests/fixtures/builtins_fixture.py")
    assert "uses_builtins" in graph
    calls = graph["uses_builtins"]
    # only user-defined helper should appear
    assert "helper" in calls
    for builtin_name in ("len", "str", "list", "range"):
        assert builtin_name not in calls, f"builtin '{builtin_name}' leaked into graph"


def test_walk_nested_functions():
    """Nested function definitions each get their own graph entry."""
    graph = walk_file("tests/fixtures/nested_funcs.py")
    assert "outer" in graph
    assert "inner" in graph
    assert "leaf" in graph
    # outer calls inner
    assert "inner" in graph["outer"]
    # inner calls leaf
    assert "leaf" in graph["inner"]


# ---------------------------------------------------------------------------
# Inline-source tests (edge cases that need no fixture file)
# ---------------------------------------------------------------------------

def test_module_level_calls_ignored():
    """Calls at module scope (not inside any function) are not recorded."""
    graph = _walk_source(
        """\
        def helper():
            pass

        helper()   # module-level call — must NOT be in any graph entry
        """
    )
    # helper itself has an entry, but no caller entry is created for the
    # module-level call site
    assert "helper" in graph
    # No entry like '' or '<module>' should exist
    assert "" not in graph
    for key in graph:
        assert key != ""


def test_empty_file():
    """An empty file produces an empty graph."""
    graph = _walk_source("")
    assert graph == {}


def test_no_calls_in_function():
    """A function that makes no calls has an empty edge list."""
    graph = _walk_source(
        """\
        def lonely():
            x = 1 + 2
            return x
        """
    )
    assert "lonely" in graph
    assert graph["lonely"] == []


def test_self_call_recorded_as_method_name():
    """self.method() inside a class records only the attribute name."""
    graph = _walk_source(
        """\
        class Foo:
            def alpha(self):
                self.beta()

            def beta(self):
                pass
        """
    )
    assert "Foo.alpha" in graph
    assert "Foo.beta" in graph
    assert "beta" in graph["Foo.alpha"]


def test_other_object_attribute_call_ignored():
    """Calls like obj.method() where obj != self are not recorded."""
    graph = _walk_source(
        """\
        def do_work(obj):
            obj.run()
            other.helper()
        """
    )
    assert "do_work" in graph
    # obj.run() and other.helper() should not appear
    assert graph["do_work"] == []


def test_chained_calls_not_recorded():
    """Chained attribute access (a.b.c()) is not recorded (too ambiguous)."""
    graph = _walk_source(
        """\
        def go():
            a.b.c()
        """
    )
    assert "go" in graph
    assert graph["go"] == []


def test_duplicate_calls_recorded():
    """The same callee called twice appears twice in the edge list."""
    graph = _walk_source(
        """\
        def repeat():
            helper()
            helper()

        def helper():
            pass
        """
    )
    assert graph["repeat"].count("helper") == 2


# ---------------------------------------------------------------------------
# Unit tests for internal helpers
# ---------------------------------------------------------------------------

def test_extract_name_bare_name():
    """_extract_name returns the function name for a bare Name node."""
    node = ast.parse("foo()").body[0].value
    assert _extract_name(node.func, "") == "foo"


def test_extract_name_builtin_filtered():
    """_extract_name returns '' for a call to a known builtin."""
    node = ast.parse("len([])").body[0].value
    assert _extract_name(node.func, "") == ""


def test_extract_name_self_attribute():
    """_extract_name returns the attr name for a self.x call inside a class."""
    node = ast.parse("self.bar()").body[0].value
    assert _extract_name(node.func, "MyClass") == "bar"


def test_extract_name_self_outside_class():
    """self.x outside a class context returns '' (no current_class)."""
    node = ast.parse("self.bar()").body[0].value
    assert _extract_name(node.func, "") == ""


def test_extract_name_other_attribute():
    """_extract_name returns '' for non-self attribute calls."""
    node = ast.parse("obj.method()").body[0].value
    assert _extract_name(node.func, "MyClass") == ""


def test_call_collector_empty_module():
    """_CallCollector on an empty module produces an empty graph."""
    tree = ast.parse("")
    collector = _CallCollector()
    collector.visit(tree)
    assert collector.graph == {}
