"""Tests for output formatters."""

import json

from mini_tracer.formats.dot import to_dot
from mini_tracer.formats.json_out import to_json
from mini_tracer.formats.mermaid import to_mermaid


def test_json_format():
    """Test JSON output format."""
    graph = {"foo": ["bar", "baz"], "bar": []}
    output = to_json(graph)
    parsed = json.loads(output)
    assert parsed == graph


def test_json_empty():
    """Test JSON output with empty graph."""
    output = to_json({})
    parsed = json.loads(output)
    assert parsed == {}


def test_mermaid_format():
    """Test Mermaid output format."""
    graph = {"foo": ["bar"], "bar": ["baz"]}
    output = to_mermaid(graph)
    assert "graph TD" in output
    assert "foo --> bar" in output
    assert "bar --> baz" in output


def test_mermaid_empty():
    """Test Mermaid output with empty graph."""
    output = to_mermaid({})
    assert "graph TD" in output


def test_dot_format():
    """Test DOT output format."""
    graph = {"foo": ["bar"], "bar": ["baz"]}
    output = to_dot(graph)
    assert "digraph G" in output
    assert '"foo" -> "bar"' in output
    assert '"bar" -> "baz"' in output


def test_dot_empty():
    """Test DOT output with empty graph."""
    output = to_dot({})
    assert "digraph G" in output
    assert "}" in output
