"""Command-line interface for mini-tracer."""

import argparse
import sys
from pathlib import Path

from mini_tracer.formats.dot import to_dot
from mini_tracer.formats.json_out import to_json
from mini_tracer.formats.mermaid import to_mermaid
from mini_tracer.resolver import resolve, walk_dir
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
    print(fmt(graph))
    return 0


def _build_graph(path: Path) -> dict[str, list[str]]:
    """Build a resolved call graph from a file or directory.

    For a single file, wraps ``walk_file`` + ``resolve``.
    For a directory, delegates to ``walk_dir`` which handles both steps.
    """
    if path.is_file():
        raw = walk_file(str(path))
        return resolve({str(path): raw})
    return walk_dir(path)


if __name__ == "__main__":
    sys.exit(main())
