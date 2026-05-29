"""Fixture that calls builtins — they should not appear in the graph."""


def uses_builtins():
    """Call several builtins that must be filtered out."""
    x = len([1, 2, 3])
    str(x)
    z = list(range(x))
    helper()
    return z


def helper():
    """Does nothing."""
    pass
