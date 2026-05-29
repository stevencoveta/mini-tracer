"""Shared helpers for format output modules."""

from __future__ import annotations


def collect_edges(graph: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Return a deduplicated, sorted list of (caller, callee) edges.

    All output formatters use this instead of re-implementing the same set
    dedup and sort logic.
    """
    seen: set[str] = set()
    edges: list[tuple[str, str]] = []
    for func_name, callees in sorted(graph.items()):
        for callee in callees:
            key = f"{func_name}\x00{callee}"
            if key not in seen:
                seen.add(key)
                edges.append((func_name, callee))
    return edges
