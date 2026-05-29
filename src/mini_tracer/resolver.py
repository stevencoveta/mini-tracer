"""Cross-file name resolution: resolve imports and map names to qualified ids."""

import ast
from pathlib import Path


def resolve(graph: dict[str, list[str]], base_dir: str = ".") -> dict[str, list[str]]:
    """Resolve unqualified names in a call graph to qualified ones.

    Builds import tables from all Python files in base_dir, then replaces
    bare function names with module-qualified names when the import table
    says they came from somewhere else (e.g. "from utils import foo" makes
    a bare "foo" resolve to "utils.foo").

    v2+ will add deeper cross-module tracking; v1 resolves via the import table.
    """
    base_path = Path(base_dir)
    import_tables = _build_import_tables(base_path)

    # Pick the table for the file that owns the caller — v1 best-effort:
    # for a simple project every caller lives in the same import universe.
    merged: dict[str, str] = {}
    for table in import_tables.values():
        merged.update(table)

    resolved: dict[str, list[str]] = {}
    for func_name, callees in graph.items():
        resolved_callees = []
        for callee in callees:
            # Already qualified  (contains a dot) is left alone.
            if "." not in callee and callee in merged:
                resolved_callees.append(merged[callee])
            else:
                resolved_callees.append(callee)
        resolved[func_name] = resolved_callees

    return resolved


def _build_import_tables(base_dir: Path) -> dict[str, dict[str, str]]:
    """Build a map of module filepath -> {imported_name -> qualified_name}."""
    import_tables: dict[str, dict[str, str]] = {}

    for py_file in base_dir.glob("**/*.py"):
        try:
            with open(py_file, encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, OSError):
            continue

        import_table: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    if alias.name == "*":
                        continue
                    qualified = f"{module}.{alias.name}" if module else alias.name
                    # Intra-repo relative import heuristic: strip .. prefix.
                    if qualified.startswith("."):
                        qualified = qualified.lstrip(".")
                    import_table[name] = qualified
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    import_table[name] = alias.name

        import_tables[str(py_file)] = import_table

    return import_tables
