"""Mermaid flowchart output formatter."""

from mini_tracer.formats._render import collect_edges


def to_mermaid(graph: dict[str, list[str]]) -> str:
    """Emit call graph as Mermaid flowchart syntax."""
    lines = ["graph TD"]
    edges = collect_edges(graph)
    if not edges:
        lines.append("    (empty)")
    for func_name, callee in edges:
        lines.append(f"    {func_name} --> {callee}")
    return "\n".join(lines)
