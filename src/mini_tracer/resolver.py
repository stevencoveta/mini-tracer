"""Cross-file resolution: map names to qualified identifiers."""

import os

from .walker import walk_file


def resolve_calls(
    calls: dict[str, list[str]], definitions: dict[str, str], module_name: str
) -> dict[str, list[str]]:
    """
    Resolve unqualified call names to qualified names.

    Args:
        calls: dict of qualified function names to list of unqualified callees
        definitions: dict of unqualified names to their qualified identifiers
        module_name: the current module name for context

    Returns:
        A copy of calls with unqualified names resolved to qualified ones.
    """
    resolved = {}

    for caller, callee_names in calls.items():
        resolved[caller] = []
        for callee in callee_names:
            resolved_name = _resolve_name(
                callee, definitions, module_name, caller
            )
            resolved[caller].append(resolved_name)

    return resolved


def _resolve_name(
    name: str, definitions: dict[str, str], module_name: str, caller: str
) -> str:
    """Resolve a single name to its qualified form."""
    # Direct match in definitions
    if name in definitions:
        return definitions[name]

    # Attribute access (e.g., obj.method)
    if "." in name:
        return name

    # Unresolved name
    return name


def walk_directory(dirpath: str) -> tuple[dict[str, list[str]], dict[str, str]]:
    """
    Recursively walk a directory and extract all call graphs.

    Args:
        dirpath: path to directory to scan

    Returns:
        A tuple of (aggregated_calls, module_map) where:
        - aggregated_calls: merged call graph from all files
        - module_map: mapping of module names to file paths
    """
    all_calls: dict[str, list[str]] = {}
    all_defs: dict[str, str] = {}
    module_map: dict[str, str] = {}

    for root, dirs, files in os.walk(dirpath):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", ".venv")]

        for filename in files:
            if not filename.endswith(".py"):
                continue

            filepath = os.path.join(root, filename)
            module_name = _path_to_module(filepath, dirpath)

            calls, defs = walk_file(filepath)

            # Prefix all names with module name
            for caller, callee_list in calls.items():
                qualified_caller = f"{module_name}.{caller}" if module_name else caller
                all_calls[qualified_caller] = callee_list

            for name, qual_name in defs.items():
                qualified_name = f"{module_name}.{qual_name}" if module_name else qual_name
                all_defs[name] = qualified_name

            module_map[module_name] = filepath

    return all_calls, all_defs


def _path_to_module(filepath: str, basedir: str) -> str:
    """Convert file path to module name."""
    relpath = os.path.relpath(filepath, basedir)
    modpath = relpath.replace(os.sep, ".").replace(".py", "")
    if modpath.endswith(".__init__"):
        modpath = modpath[:-9]
    return modpath
