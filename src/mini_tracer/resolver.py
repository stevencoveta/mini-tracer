"""Cross-file name resolution: resolve imports and map names to qualified ids."""

import ast
from pathlib import Path


def resolve(
    graph: dict[str, list[str]], base_dir: str = "."
) -> dict[str, list[str]]:
    """
    Resolve unqualified names in a call graph to qualified ones.

    Builds import tables from all Python files in base_dir, then replaces
    bare function names like 'foo' with module-qualified names like 'module.foo'
    where possible. Falls back to bare names if resolution fails.

    Args:
        graph: Call graph with potentially unqualified names.
        base_dir: Root directory to scan for Python files (for imports).

    Returns:
        Resolved graph with qualified names where possible.
    """
    base_path = Path(base_dir)
    import_tables = _build_import_tables(base_path)
    resolved = {}

    for func_name, callees in graph.items():
        resolved_callees = []
        for callee in callees:
            resolved_name = _resolve_name(callee, func_name, import_tables)
            resolved_callees.append(resolved_name)
        resolved[func_name] = resolved_callees

    return resolved


def _build_import_tables(base_dir: Path) -> dict[str, dict[str, str]]:
    """
    Build a map of module filepath -> {imported_name -> qualified_name}.

    Args:
        base_dir: Root directory to scan for Python files.

    Returns:
        Dict mapping filepath to import table for that file.
    """
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
                    import_table[name] = f"{module}.{alias.name}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    import_table[name] = alias.name

        import_tables[str(py_file)] = import_table

    return import_tables


def _resolve_name(
    callee: str,
    caller: str,
    import_tables: dict[str, dict[str, str]],
) -> str:
    """
    Resolve a callee name using import tables.

    Simple greedy strategy: for now, just return the name as-is.
    Full import resolution across modules is v2+.

    Args:
        callee: The name being called.
        caller: The function calling it.
        import_tables: Map of import tables by filepath.

    Returns:
        Resolved name, or original if unresolved.
    """
    # v1: return callee unchanged; v2 will do proper import tracing.
    _ = caller, import_tables
    return callee
