"""AST walk to collect function/method definitions and call edges per file."""

import ast
import builtins

# Built-in names so we never emit call-graph edges for the stdlib itself.
_BUILTIN_NAMES: set[str] = set(dir(builtins)) | {
    "isinstance", "hasattr", "getattr", "setattr", "issubclass",
    "reversed", "sorted", "globals", "locals", "vars", "dir",
    "len", "repr", "str", "int", "float", "bool", "list", "dict",
    "set", "tuple", "next", "iter", "enumerate", "zip", "range",
    "map", "filter", "sum", "min", "max", "any", "all",
}


def walk_file(filepath: str) -> dict[str, list[str]]:
    """
    Walk a single Python file and extract the call graph.

    Returns a dict mapping qualified function/method name to list of
    called names.  Only programmer-written function calls are kept:
    bare names (foo()) and same-class self calls (self.bar()).
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

    collector = _CallCollector()
    collector.visit(tree)
    return collector.graph


class _CallCollector(ast.NodeVisitor):
    """Visit AST nodes and collect function definitions and calls."""

    def __init__(self):
        self.graph: dict[str, list[str]] = {}
        self.current_class: str = ""
        self.current_function: str = ""

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_func = self.current_function
        if self.current_class:
            self.current_function = f"{self.current_class}.{node.name}"
        else:
            self.current_function = node.name
        if self.current_function not in self.graph:
            self.graph[self.current_function] = []
        self.generic_visit(node)
        self.current_function = old_func

    visit_AsyncFunctionDef = visit_FunctionDef  # noqa: N815

    def visit_Call(self, node: ast.Call) -> None:
        """Record a function call: only bare names and self.x inside methods."""
        if not self.current_function:
            self.generic_visit(node)
            return

        callee = _extract_name(node.func, self.current_class)
        if callee:
            self.graph[self.current_function].append(callee)
        self.generic_visit(node)


def _extract_name(func: ast.expr, current_class: str) -> str:
    """Return callee name for a Call.func, or '' if it's not caller code.

    Rules (v1):
      - bare Name(foo)     → "foo"               (function call)
      - self.X(Y)          → "X" if in class     (same-class method call)
      - everything else    → ""                  (std lib / temp var / ...)
    """
    if isinstance(func, ast.Name):
        name = func.id
        return "" if name in _BUILTIN_NAMES else name
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name) and func.value.id == "self":
            return func.attr if current_class else ""
    return ""
