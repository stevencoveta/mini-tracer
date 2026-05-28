"""Test fixture with class methods."""


class MyClass:
    """A simple class."""

    def method_a(self):
        """Call method_b."""
        self.method_b()

    def method_b(self):
        """Call foo."""
        foo()


def foo():
    """Call bar."""
    bar()


def bar():
    """Do nothing."""
    pass
