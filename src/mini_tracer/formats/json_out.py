"""JSON output format for call graphs."""

import json


def format_json(calls: dict[str, list[str]]) -> str:
    """
    Format a call graph as JSON.

    Args:
        calls: dict mapping qualified names to lists of callees

    Returns:
        A JSON string representation of the call graph
    """
    # Sort for deterministic output
    sorted_calls = {k: sorted(v) for k, v in sorted(calls.items())}
    return json.dumps(sorted_calls, indent=2)
