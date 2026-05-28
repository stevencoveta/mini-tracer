"""Simple test fixture with function calls."""


def foo():
    """Call bar and baz."""
    bar()
    baz()


def bar():
    """Call baz."""
    baz()


def baz():
    """Does nothing."""
    pass
