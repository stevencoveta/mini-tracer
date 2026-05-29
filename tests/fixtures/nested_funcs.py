"""Fixture with nested function definitions."""


def outer():
    """Define and call an inner function."""
    def inner():
        """Call leaf."""
        leaf()

    inner()


def leaf():
    """Does nothing."""
    pass
