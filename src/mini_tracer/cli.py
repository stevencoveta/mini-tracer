"""Command-line interface for mini-tracer."""

import argparse
import sys
from pathlib import Path

from mini_tracer.formats.dot import to_dot
from mini_tracer.formats.json_out import to_json
from mini_tracer.formats.mermaid import to_mermaid
from mini_tracer.resolver import resolve
from mini_tracer.walker import walk_file

_FORMATTERS: dict[str, object] = {
    "json": to_json,
    "mermaid": to_mermaid,
    "dot": to_dot,
}


def main() -> int:
    """Parse arguments and emit call graph in requested format."""
    parser = argparse.ArgumentParser(
        prog="mini-tracer",
        description="Static Python call-graph extractor.",
    )
    parser.add_argument(
        "path",
        help="Path to a .py file or directory to analyze.",
    )
    parser.add_argument(
        "--format",
        choices=list(_FORMATTERS),
        default="json",
        help="Output format (default: json).",
    )

    args = parser.parse_args()
    path = Path(args.path)
    fmt = _FORMATTERS[args.format]

    if not path.exists():
        print(f"Error: path does not exist: {path}", file=sys.stderr)
        return 1

    graph = _build_graph(path)
    resolved = (
        resolve(graph, str(path.parent if path.is_file() else path))
    ) if graph else graph
    print(fmt(resolved))
    return 0


def _build_graph(path: Path) -> dict[str, list[str]]:
    """Build call graph from a file or directory.

    Duplicate edges across files are removed."""
    if path.is_file():
        return walk_file(str(path))

    graph: dict[str, list[str]] = {}
    for py_file in path.rglob("*.py"):
        file_graph = walk_file(str(py_file))
        for func, callees in file_graph.items():
            if func not in graph:
                graph[func] = []
            # O(n) dedup — cheap for small graphs (typical v1 use).
            seen = set(graph[func])
            for c in callees:
                if c not in seen:
                    seen.add(c)
                    graph[func].append(c)
    return graph


if __name__ == "__main__":
    sys.exit(main())
