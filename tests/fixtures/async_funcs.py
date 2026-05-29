"""Fixture with async functions to verify they are collected like sync ones."""


async def fetch():
    """Call process."""
    process()


async def process():
    """Call helper."""
    helper()


def helper():
    """Does nothing."""
    pass
