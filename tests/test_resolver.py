"""Tests for the resolver module."""

from mini_tracer.resolver import resolve


def test_resolve_simple():
    """Test resolving a simple graph with no imports."""
    graph = {"foo": ["bar"], "bar": ["baz"], "baz": []}
    resolved = resolve(graph, ".")
    # In v1, resolution is minimal, so the graph should remain unchanged
    assert resolved == graph


def test_resolve_with_qualified_names():
    """Test resolving a graph that already has qualified names."""
    graph = {"MyClass.method": ["other.func", "foo"], "foo": []}
    resolved = resolve(graph, ".")
    # In v1, we don't do full import resolution yet
    assert "MyClass.method" in resolved
    assert resolved["MyClass.method"] == ["other.func", "foo"]


def test_resolve_empty_graph():
    """Test resolving an empty graph."""
    resolved = resolve({}, ".")
    assert resolved == {}
