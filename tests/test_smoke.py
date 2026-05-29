"""Smoke test: running mini-tracer on its own source must not emit built-in noise.

This is the acceptance gate that proved the project is a real tool, not a
scaffold that dumps `isinstance`, `str`, `print` into the graph."""

from pathlib import Path

from mini_tracer.cli import _build_graph


def test_on_own_source_no_builtin_noise():
    """The call graph for mini-tracer itself must not contain stdlib names."""
    graph = _build_graph(Path("src/mini_tracer"))
    builtins = {"isinstance", "print", "str", "list", "dict", "set", "int",
                "reversed", "json.dumps", "sorted", "open", "ast.parse",
                "ast.walk", "glob", "read", "write", "close",
                "items", "keys", "values", "path.glob"}

    all_names = set(graph)
    for callees in graph.values():
        all_names.update(callees)

    bad = all_names & builtins
    if bad:
        raise AssertionError(
            f"Graph contains {len(bad)} built-in names: {bad}"
        )
