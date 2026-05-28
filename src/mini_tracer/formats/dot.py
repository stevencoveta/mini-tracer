"""Graphviz DOT output formatter."""



def to_dot(graph: dict[str, list[str]]) -> str:
    """
    Emit call graph as Graphviz DOT syntax.

    Args:
        graph: Call graph dict.

    Returns:
        DOT format string suitable for `dot -Tpng`.
    """
    lines = ['digraph G {']
    edges: set[str] = set()

    for func_name, callees in sorted(graph.items()):
        for callee in callees:
            edge = f'    "{func_name}" -> "{callee}";'
            if edge not in edges:
                edges.add(edge)
                lines.append(edge)

    lines.append('}')
    return '\n'.join(lines)
