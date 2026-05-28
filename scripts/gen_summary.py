"""Generate codebase summary markdown from AST introspection."""

import ast
import os


def _get_description() -> str:
    """Read the project description from pyproject.toml."""
    pyproject_path = os.path.join(
        os.path.dirname(__file__), "..", "pyproject.toml"
    )
    with open(pyproject_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith('description = "'):
                # Extract quoted string
                return line.split('description = "', 1)[1].rstrip('"\n')
    return "mini-tracer: static Python call graph extractor"


def _first_docstring(node: ast.AST) -> str | None:
    """Extract the first line of a docstring from an AST node."""
    docstring = ast.get_docstring(node)
    if docstring:
        return docstring.split("\n")[0].strip()
    return None


def _public_symbols(module_path: str) -> set[str]:
    """Extract public (non-underscore) symbols from a module."""
    if not os.path.isfile(module_path):
        return set()

    try:
        with open(module_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), module_path)
    except SyntaxError:
        return set()

    symbols = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                symbols.add(node.name)

    return symbols


def _sibling_imports(module_path: str, src_root: str) -> set[str]:
    """Extract sibling module imports from a module."""
    if not os.path.isfile(module_path):
        return set()

    try:
        with open(module_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), module_path)
    except SyntaxError:
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("mini_tracer"):
                imports.add(node.module)

    return imports


def _get_arg_names(args: ast.arguments) -> list[str]:
    """Extract argument names from ast.arguments."""
    arg_names = []
    for arg in args.posonlyargs:
        arg_names.append(arg.arg)
    for arg in args.args:
        arg_names.append(arg.arg)
    if args.vararg:
        arg_names.append(f"*{args.vararg.arg}")
    for arg in args.kwonlyargs:
        arg_names.append(arg.arg)
    if args.kwarg:
        arg_names.append(f"**{args.kwarg.arg}")
    return arg_names


def _function_signature(node: ast.FunctionDef) -> str:
    """Build function signature from AST node."""
    arg_names = _get_arg_names(node.args)
    args_str = ", ".join(arg_names)
    
    # Try to determine return type from annotation
    if node.returns:
        # We don't have the full type string, so just indicate there's a return type
        return f"({args_str})"
    return f"({args_str})"


def _collect_functions_and_classes(
    module_path: str,
) -> list[tuple[str, str, str, str | None]]:
    """
    Extract all top-level functions and classes with signatures and docstrings.

    Returns:
        List of tuples: (type, name, sig, docstring_first_line)
        where type is 'function', 'async function', 'method', 'async method', or 'class'
    """
    if not os.path.isfile(module_path):
        return []

    try:
        with open(module_path, encoding="utf-8") as f:
            source = f.read()
            tree = ast.parse(source, module_path)
    except SyntaxError:
        return []

    items = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            sig = _function_signature(node)
            docstring = _first_docstring(node)
            items.append(("function", node.name, sig, docstring))

        elif isinstance(node, ast.AsyncFunctionDef):
            sig = _function_signature(node)
            docstring = _first_docstring(node)
            items.append(("async function", node.name, sig, docstring))

        elif isinstance(node, ast.ClassDef):
            docstring = _first_docstring(node)
            items.append(("class", node.name, "", docstring))

            # List methods of the class
            for method in node.body:
                if isinstance(method, ast.FunctionDef):
                    sig = _function_signature(method)
                    method_docstring = _first_docstring(method)
                    items.append(
                        (
                            "method",
                            f"{node.name}.{method.name}",
                            sig,
                            method_docstring,
                        )
                    )
                elif isinstance(method, ast.AsyncFunctionDef):
                    sig = _function_signature(method)
                    method_docstring = _first_docstring(method)
                    items.append(
                        (
                            "async method",
                            f"{node.name}.{method.name}",
                            sig,
                            method_docstring,
                        )
                    )

    return items


def _get_section_heading_name(rel_path: str) -> str:
    """Convert a file path to a section heading name."""
    # rel_path is like "walker.py" or "formats/dot.py"
    # For __init__.py in root, use "main"
    # For formats/__init__.py, use "formats"
    # For formats/dot.py, use "dot" (or "formats/dot"?)
    
    if rel_path == "__init__.py":
        return "mini_tracer"
    
    # Remove .py extension
    base = rel_path[:-3] if rel_path.endswith(".py") else rel_path
    
    # For formats/__init__.py, return "formats"
    if base == "formats/__init__" or base == "formats/__init__":
        return "formats"
    
    # For formats/X.py, return just X for simplicity
    if "/" in base:
        parts = base.split("/")
        if parts[-1] == "__init__":
            return parts[0]
        return parts[-1]
    
    return base


def collect_modules(src_root: str) -> list[dict]:
    """
    Walk src_root and gather metadata for every .py file in the package.

    Returns:
        List of dicts with keys: module_path, purpose, public_symbols, items
    """
    modules = []

    for root, dirs, files in os.walk(src_root):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != "__pycache__"]

        for filename in sorted(files):
            if not filename.endswith(".py"):
                continue

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, src_root)

            # Convert path to module name
            if filename == "__init__.py":
                if root == src_root:
                    module_name = "mini_tracer"
                else:
                    rel_dir = os.path.relpath(root, src_root)
                    module_name = "mini_tracer." + rel_dir.replace(os.sep, ".")
            else:
                module_name_part = filename[:-3]  # Strip .py
                if root == src_root:
                    module_name = "mini_tracer." + module_name_part
                else:
                    rel_dir = os.path.relpath(root, src_root)
                    module_name = (
                        "mini_tracer."
                        + rel_dir.replace(os.sep, ".")
                        + "."
                        + module_name_part
                    )

            # Read docstring
            try:
                with open(filepath, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filepath)
                    purpose = ast.get_docstring(tree)
                    if purpose:
                        purpose = purpose.split("\n")[0].strip()
                    else:
                        purpose = "—"
            except SyntaxError:
                purpose = "—"

            public_symbols = sorted(_public_symbols(filepath))
            items = _collect_functions_and_classes(filepath)

            modules.append(
                {
                    "rel_path": rel_path,
                    "module_name": module_name,
                    "purpose": purpose,
                    "public_symbols": public_symbols,
                    "items": items,
                }
            )

    return modules


def _render_module_table(modules: list[dict]) -> str:
    """Render the module table."""
    lines = ["## Module Overview\n"]
    lines.append("| Module | Purpose | Public Symbols |")
    lines.append("|--------|---------|----------------|")

    for mod in modules:
        rel_path = mod["rel_path"].replace(os.sep, "/")
        purpose = mod["purpose"] if mod["purpose"] != "—" else "—"
        symbols = ", ".join(mod["public_symbols"]) if mod["public_symbols"] else "—"
        lines.append(f"| `{rel_path}` | {purpose} | {symbols} |")

    return "\n".join(lines)


def _render_dependency_matrix(modules: list[dict], src_root: str) -> str:
    """Render the dependency matrix."""
    lines = ["## Dependency Matrix\n"]
    lines.append(
        "Shows which modules import which sibling modules (mini_tracer.*):\n"
    )

    # Get all unique module short names for matrix
    all_modules = list(modules)
    short_names = []
    for m in all_modules:
        # Get short name (last component)
        full = m["module_name"]
        if full == "mini_tracer":
            short_names.append("__init__")
        else:
            short_names.append(full.split(".")[-1])

    # Build matrix
    matrix_lines = ["| | " + " | ".join(short_names) + " |"]
    matrix_lines.append("|---" + ("|---" * len(short_names)) + "|")

    for i, mod in enumerate(all_modules):
        imports = _sibling_imports(
            os.path.join(src_root, mod["rel_path"]), src_root
        )

        row = [short_names[i]]
        for _j, other in enumerate(all_modules):
            other_module = other["module_name"]
            if other_module in imports:
                row.append("✓")
            else:
                row.append("")

        matrix_lines.append("| " + " | ".join(row) + " |")

    return "\n".join(matrix_lines)


def _render_per_module_sections(modules: list[dict]) -> str:
    """Render detailed per-module sections."""
    lines = []

    for mod in modules:
        rel_path = mod["rel_path"].replace(os.sep, "/")
        heading_name = _get_section_heading_name(rel_path)
        lines.append(f"## {heading_name}\n")

        purpose = mod["purpose"]
        if purpose != "—":
            lines.append(f"{purpose}\n")

        if not mod["items"]:
            lines.append("_(no public definitions)_\n")
        else:
            for item_type, name, sig, docstring in mod["items"]:
                if item_type == "class":
                    lines.append(f"### class `{name}`\n")
                elif item_type == "method":
                    lines.append(f"### `{name}{sig}`\n")
                elif item_type == "async method":
                    lines.append(f"### `async {name}{sig}`\n")
                elif item_type == "async function":
                    lines.append(f"### `async {name}{sig}`\n")
                else:  # function
                    lines.append(f"### `{name}{sig}`\n")

                if docstring:
                    lines.append(f"{docstring}\n")
                lines.append("")

    return "\n".join(lines)


def render(modules: list[dict], src_root: str) -> str:
    """Render the complete markdown document."""
    parts = []

    # Header with project description
    description = _get_description()
    parts.append(f"# mini-tracer Codebase\n\n{description}\n\n---\n")

    # Module overview table
    parts.append(_render_module_table(modules))
    parts.append("\n---\n")

    # Dependency matrix
    parts.append(_render_dependency_matrix(modules, src_root))
    parts.append("\n---\n")

    # Per-module sections
    parts.append(_render_per_module_sections(modules))

    return "\n".join(parts)


def main() -> None:
    """Main entry point: walk src/mini_tracer and write docs/codebase_summary.md."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    src_root = os.path.join(repo_root, "src", "mini_tracer")
    output_dir = os.path.join(repo_root, "docs")
    output_file = os.path.join(output_dir, "codebase_summary.md")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Collect module metadata
    modules = collect_modules(src_root)

    # Render markdown
    markdown = render(modules, src_root)

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Generated {output_file}")


if __name__ == "__main__":
    main()
