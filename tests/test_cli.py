"""Tests for the CLI module."""

from pathlib import Path

from mini_tracer.cli import _build_graph


def test_build_graph_single_file():
    """Test building graph from a single file."""
    graph = _build_graph(Path("tests/fixtures/simple.py"))
    assert "foo" in graph
    assert "bar" in graph
    assert "baz" in graph


def test_build_graph_directory():
    """Test building graph from a directory."""
    graph = _build_graph(Path("tests/fixtures"))
    assert len(graph) > 0


def test_build_graph_nonexistent():
    """Test building graph from nonexistent path."""
    graph = _build_graph(Path("tests/fixtures/nonexistent.py"))
    assert graph == {}
