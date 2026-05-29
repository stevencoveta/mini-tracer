"""Cross-file name resolution: merge per-file graphs and qualify import edges."""

import ast
from pathlib import Path

from mini_tracer.walker import walk_file


def resolve(
    file_graphs: dict[str, dict[str, list[str]]],
) -> dict[str, list[str]]:
    """Merge per-file call graphs and resolve imported names to qualified ids.

    Each key in *file_graphs* is a file path; the value is the raw graph
    returned by ``walk_file`` for that file.  The function:

    1. Builds an import table for every file (``from b import foo`` →
       ``{"foo": "b.foo"}``).
    2. For each caller's callee list, replaces bare names that appear in
       *that file's* import table with their qualified counterpart
       (e.g. ``"foo"`` → ``"b.foo"``).
    3. Merges all per-file graphs into a single flat dict keyed by the
       qualified function name.  Callees that cannot be resolved are kept
       verbatim.

    Returns a dict mapping qualified caller name → list of (possibly
    qualified) callee names.
    """
    # Build per-file import tables first.
    import_tables: dict[str, dict[str, str]] = {
        filepath: _build_import_table(filepath)
        for filepath in file_graphs
    }

    merged: dict[str, list[str]] = {}
    for filepath, graph in file_graphs.items():
        table = import_tables.get(filepath, {})
        for func_name, callees in graph.items():
            resolved_callees = [
                table[callee] if ("." not in callee and callee in table) else callee
                for callee in callees
            ]
            merged[func_name] = resolved_callees

    return merged


def walk_dir(root: str | Path) -> dict[str, list[str]]:
    """Recursively walk *root* and return a merged, resolved call graph.

    Finds every ``.py`` file under *root*, calls ``walk_file`` on each to
    get a raw per-file graph, then passes all graphs to ``resolve`` and
    returns the combined result.
    """
    root_path = Path(root)
    file_graphs: dict[str, dict[str, list[str]]] = {}
    for py_file in sorted(root_path.glob("**/*.py")):
        graph = walk_file(str(py_file))
        if graph:  # skip empty (syntax errors / empty files)
            file_graphs[str(py_file)] = graph
    return resolve(file_graphs)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_import_table(filepath: str) -> dict[str, str]:
    """Parse *filepath* and return a mapping of local name → qualified name.

    For ``from b import foo`` the entry is ``{"foo": "b.foo"}``.
    For ``import os`` the entry is ``{"os": "os"}``.
    For ``import os as operating_system`` the entry is
    ``{"operating_system": "os"}``.
    Names that cannot be parsed or that use star-imports are skipped.
    """
    try:
        with open(filepath, encoding="utf-8") as fh:
            source = fh.read()
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return {}

    table: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if alias.name == "*":
                    continue
                local_name = alias.asname if alias.asname else alias.name
                qualified = f"{module}.{alias.name}" if module else alias.name
                table[local_name] = qualified
        elif isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname if alias.asname else alias.name
                table[local_name] = alias.name

    return table
