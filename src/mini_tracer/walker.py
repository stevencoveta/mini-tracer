"""AST walk to collect function/method definitions and call edges per file."""

import ast


def walk_file(filepath: str) -> dict[str, list[str]]:
    """
    Walk a single Python file and extract the call graph.

    Args:
        filepath: Path to a .py file.

    Returns:
        Dict mapping qualified function/method name to list of called names.
        E.g. {'foo': ['bar', 'baz'], 'MyClass.method': ['foo', 'other.func']}
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
    except OSError:
        return {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    collector = CallCollector(filepath)
    collector.visit(tree)
    return collector.graph


class CallCollector(ast.NodeVisitor):
    """Visit AST nodes and collect function definitions and calls."""

    def __init__(self, filepath: str):
        """Initialise with the file path being analysed."""
        self.filepath = filepath
        self.graph: dict[str, list[str]] = {}
        self.current_class: str = ""
        self.current_function: str = ""

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Record class and visit methods inside it."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Record function/method definition and collect calls in its body."""
        old_func = self.current_function
        if self.current_class:
            self.current_function = f"{self.current_class}.{node.name}"
        else:
            self.current_function = node.name
        if self.current_function not in self.graph:
            self.graph[self.current_function] = []
        self.generic_visit(node)
        self.current_function = old_func

    # ast.NodeVisitor requires camelCase method names to match AST node names.
    visit_AsyncFunctionDef = visit_FunctionDef  # noqa: N815

    def visit_Call(self, node: ast.Call) -> None:
        """Record a function call."""
        if not self.current_function:
            self.generic_visit(node)
            return
        callee = self._extract_name(node.func)
        # Inside a class, self.method_b() resolves to method_b.
        if callee and self.current_class and callee.startswith("self."):
            callee = callee[5:]
        if callee:
            self.graph[self.current_function].append(callee)
        self.generic_visit(node)

    def _extract_name(self, node: ast.expr) -> str:
        """Extract function name from a Call node's func attribute."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
                return ".".join(reversed(parts))
        return ""
