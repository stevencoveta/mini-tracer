"""Graphviz DOT output formatter."""

from mini_tracer.formats._render import collect_edges


def to_dot(graph: dict[str, list[str]]) -> str:
    """Emit call graph as Graphviz DOT syntax."""
    lines = ["digraph G {"]
    for func_name, callee in collect_edges(graph):
        lines.append(f'    "{func_name}" -> "{callee}";')
    lines.append("}")
    return "\n".join(lines)
