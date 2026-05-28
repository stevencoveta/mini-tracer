"""JSON output formatter."""

import json


def to_json(graph: dict[str, list[str]], indent: int = 2) -> str:
    """
    Emit call graph as JSON.

    Args:
        graph: Call graph dict.
        indent: JSON indentation (default 2).

    Returns:
        JSON string representation of the graph.
    """
    return json.dumps(graph, indent=indent, sort_keys=True)
