"""Command-line interface for mini-tracer."""

import argparse
import sys
from pathlib import Path

from mini_tracer.formats.dot import to_dot
from mini_tracer.formats.json_out import to_json
from mini_tracer.formats.mermaid import to_mermaid
from mini_tracer.resolver import resolve
from mini_tracer.walker import walk_file


def main() -> int:
    """
    Parse arguments and emit call graph in requested format.

    Returns:
        Exit code (0 on success, 1 on error).
    """
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
        choices=["json", "mermaid", "dot"],
        default="json",
        help="Output format (default: json).",
    )

    args = parser.parse_args()

    path = Path(args.path)

    if not path.exists():
        print(f"Error: path does not exist: {path}", file=sys.stderr)
        return 1

    graph = _build_graph(path)

    if not graph:
        # Empty graph case
        if args.format == "json":
            output = to_json({})
        elif args.format == "mermaid":
            output = to_mermaid({})
        else:  # dot
            output = to_dot({})
    else:
        resolved = resolve(graph, str(path.parent if path.is_file() else path))
        if args.format == "json":
            output = to_json(resolved)
        elif args.format == "mermaid":
            output = to_mermaid(resolved)
        else:  # dot
            output = to_dot(resolved)

    print(output)
    return 0


def _build_graph(path: Path) -> dict[str, list[str]]:
    """
    Build call graph from a file or directory.

    Args:
        path: File or directory path.

    Returns:
        Merged call graph from all Python files found.
    """
    graph: dict[str, list[str]] = {}

    if path.is_file():
        return walk_file(str(path))

    for py_file in path.glob("**/*.py"):
        file_graph = walk_file(str(py_file))
        for func, callees in file_graph.items():
            if func not in graph:
                graph[func] = []
            graph[func].extend(callees)

    return graph


if __name__ == "__main__":
    sys.exit(main())
