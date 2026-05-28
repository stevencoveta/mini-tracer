"""argparse-based CLI entry point for mini-tracer."""

import argparse
import os
import sys

from .formats.dot import format_dot
from .formats.json_out import format_json
from .formats.mermaid import format_mermaid
from .resolver import resolve_calls, walk_directory
from .walker import walk_file


def _build_graph(target: str) -> dict[str, list[str]]:
    """Build a call graph from a file or directory path."""
    if os.path.isdir(target):
        calls, defs = walk_directory(target)
    elif os.path.isfile(target):
        calls, defs = walk_file(target)
        calls = resolve_calls(calls, defs, module_name="")
    else:
        print(f"error: {target!r} is not a file or directory", file=sys.stderr)
        sys.exit(1)
    return calls


def main() -> None:
    """Parse arguments, build the call graph, and emit the chosen format."""
    parser = argparse.ArgumentParser(
        prog="mini-tracer",
        description="Static call-graph extractor for Python source files.",
    )
    parser.add_argument(
        "target",
        help="Path to a .py file or a directory to scan recursively.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "mermaid", "dot"],
        default="json",
        help="Output format (default: json).",
    )
    args = parser.parse_args()

    calls = _build_graph(args.target)

    if args.format == "json":
        print(format_json(calls))
    elif args.format == "mermaid":
        print(format_mermaid(calls))
    elif args.format == "dot":
        print(format_dot(calls))


if __name__ == "__main__":
    main()
