"""Mermaid output format for call graphs."""



def format_mermaid(calls: dict[str, list[str]]) -> str:
    """
    Format a call graph as Mermaid graph TD syntax.

    Args:
        calls: dict mapping qualified names to lists of callees

    Returns:
        A Mermaid graph TD block
    """
    lines = ["graph TD"]

    # Track unique edges to avoid duplicates
    edges: set = set()

    for caller, callees in sorted(calls.items()):
        for callee in sorted(set(callees)):
            # Skip self-loops and empty names
            if not callee or callee == caller:
                continue

            # Mermaid node IDs must be valid identifiers, so sanitize
            caller_id = _sanitize_id(caller)
            callee_id = _sanitize_id(callee)

            edge = (caller_id, callee_id, caller, callee)
            edges.add(edge)

    for caller_id, callee_id, caller_label, callee_label in sorted(edges):
        lines.append(f'    {caller_id}["{caller_label}"]')
        lines.append(f'    {callee_id}["{callee_label}"]')
        lines.append(f"    {caller_id} --> {callee_id}")

    return "\n".join(lines)


def _sanitize_id(name: str) -> str:
    """Convert a qualified name to a valid Mermaid node ID."""
    # Replace dots and special chars with underscores
    sanitized = name.replace(".", "_").replace("-", "_")
    sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in sanitized)
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized or "_empty"
