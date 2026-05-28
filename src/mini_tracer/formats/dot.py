"""Graphviz DOT output format for call graphs."""



def format_dot(calls: dict[str, list[str]]) -> str:
    """
    Format a call graph as Graphviz DOT.

    Args:
        calls: dict mapping qualified names to lists of callees

    Returns:
        A DOT format graph
    """
    lines = ['digraph CallGraph {', '    rankdir=LR;']

    # Track unique edges
    edges: set = set()

    for caller, callees in sorted(calls.items()):
        for callee in sorted(set(callees)):
            # Skip self-loops and empty names
            if not callee or callee == caller:
                continue

            edge = (caller, callee)
            edges.add(edge)

    # Add nodes and edges
    for caller, callee in sorted(edges):
        lines.append(f'    "{caller}" -> "{callee}";')

    lines.append("}")
    return "\n".join(lines)
