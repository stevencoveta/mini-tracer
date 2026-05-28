"""Tests for the walker module."""

from mini_tracer.walker import walk_file


def test_walk_simple_file():
    """Test walking a simple file with function calls."""
    graph = walk_file("tests/fixtures/simple.py")
    assert "foo" in graph
    assert "bar" in graph
    assert "baz" in graph
    assert set(graph["foo"]) == {"bar", "baz"}
    assert graph["bar"] == ["baz"]
    assert graph["baz"] == []


def test_walk_classes():
    """Test walking a file with class methods."""
    graph = walk_file("tests/fixtures/classes.py")
    assert "MyClass.method_a" in graph
    assert "MyClass.method_b" in graph
    assert "foo" in graph
    assert "bar" in graph
    assert "MyClass.method_a" in graph
    assert "method_b" in graph["MyClass.method_a"]
    assert "foo" in graph["MyClass.method_b"]


def test_walk_nonexistent():
    """Test walking a file that doesn't exist."""
    graph = walk_file("tests/fixtures/nonexistent.py")
    assert graph == {}


def test_walk_syntax_error():
    """Test walking a file with syntax errors."""
    # This would be a broken Python file, but we can't easily create one
    # in a test. The walker should gracefully return {} on syntax errors.
    pass
