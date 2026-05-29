"""JSON output formatter."""

import json


def to_json(graph: dict[str, list[str]], indent: int = 2) -> str:
    """Emit call graph as JSON.

    No dedup is needed here — dict naturally suppresses duplicate keys,
    and we expect callers to have already used the standard list form.
    """
    return json.dumps(graph, indent=indent, sort_keys=True)
