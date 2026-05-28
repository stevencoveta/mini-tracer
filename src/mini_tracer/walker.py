"""AST walk: collect function/method definitions and calls per file."""

import ast


def walk_file(filepath: str) -> tuple[dict[str, list[str]], dict[str, str]]:
    """
    Parse a Python file and extract call graph.

    Returns:
        A tuple of (calls, definitions) where:
        - calls: dict mapping qualified names to list of names they call
        - definitions: dict mapping unqualified names to their scope
    """
    with open(filepath, encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source, filepath)
    except SyntaxError:
        return {}, {}

    calls: dict[str, list[str]] = {}
    definitions: dict[str, str] = {}

    visitor = CallGraphVisitor(calls, definitions)
    visitor.visit(tree)

    return calls, definitions


class CallGraphVisitor(ast.NodeVisitor):
    """Extract function/method definitions and their call sites."""

    def __init__(
        self, calls: dict[str, list[str]], definitions: dict[str, str]
    ) -> None:
        """Initialize visitor with storage for calls and definitions."""
        self.calls = calls
        self.definitions = definitions
        self.scope_stack: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition."""
        qualified_name = ".".join([*self.scope_stack, node.name])
        self.definitions[node.name] = qualified_name

        if qualified_name not in self.calls:
            self.calls[qualified_name] = []

        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an async function definition."""
        qualified_name = ".".join([*self.scope_stack, node.name])
        self.definitions[node.name] = qualified_name

        if qualified_name not in self.calls:
            self.calls[qualified_name] = []

        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition."""
        self.definitions[node.name] = ".".join([*self.scope_stack, node.name])
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        """Visit a function call and record it."""
        if self.scope_stack:
            caller = ".".join(self.scope_stack)
            if caller not in self.calls:
                self.calls[caller] = []

            callee_name = self._extract_name(node.func)
            if callee_name:
                self.calls[caller].append(callee_name)

        self.generic_visit(node)

    def _extract_name(self, node: ast.expr) -> str:
        """Extract a callable name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            value_name = self._extract_name(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
        return ""
