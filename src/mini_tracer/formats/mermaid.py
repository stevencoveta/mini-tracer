"""Mermaid flowchart output formatter."""



def to_mermaid(graph: dict[str, list[str]]) -> str:
    """
    Emit call graph as Mermaid flowchart syntax.

    Args:
        graph: Call graph dict.

    Returns:
        Mermaid graph string.
    """
    lines = ["graph TD"]
    edges: set[str] = set()

    for func_name, callees in sorted(graph.items()):
        for callee in callees:
            edge_id = f"{func_name} --> {callee}"
            if edge_id not in edges:
                edges.add(edge_id)
                lines.append(f"    {func_name} --> {callee}")

    return "\n".join(lines) if edges else "graph TD\n    (empty)"
