"""Subgraph context builder — extract targeted code context for agent consumption.

Given a target symbol (function, method, class), returns a compact markdown
summary of:
  - the symbol's own definition (from its source file)
  - its callees up to depth N
  - its callers up to depth M
  - any other symbols in the same file that are NOT connected (for file-scope context)

The output is designed to be < 6,000 tokens so it fits comfortably in the
agent's context window alongside the system prompt + card text.

Uses the resolved graph from ``resolver.resolve`` / ``resolver.walk_dir``.
"""

from __future__ import annotations

import ast
from pathlib import Path

from mini_tracer.resolver import walk_dir

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_context(
    target: str,
    repo_root: str | Path = ".",
    *,
    callee_depth: int = 2,
    caller_depth: int = 1,
    max_tokens: int = 6000,
) -> str:
    """Return a focused context string for *target*.

    Parameters
    ----------
    target
        Qualified symbol name, e.g. ``"resolve"``, ``"resolver.resolve"``,
        ``"MyClass.method_a"``.
    repo_root
        Directory to scan (passed to ``walk_dir``).
    callee_depth
        How many hops down the call graph to follow from *target*.
    caller_depth
        How many hops up the call graph to follow toward *target*.
    max_tokens
        Rough ceiling — the function trims aggressively once the
        token estimate exceeds this.

    Returns
    -------
    str
        Markdown with sections:
        ``## Target: <name>``, ``## Callees``, ``## Callers``,
        ``## Same-file neighbors``.
    """
    repo = Path(repo_root)
    graph = walk_dir(repo)
    if not graph:
        return f"_No call-graph data found in {repo}._\n"

    # Build bidirectional adjacency
    callers = _build_callers(graph)
    callees = graph

    # Resolve target to a graph key (exact match or suffix match)
    target_key = _resolve_target(target, set(graph))
    if target_key is None:
        return f"_Symbol `{target}` not found in call graph._\n"

    # Collect relevant symbols
    scope = _collect_scope(
        target_key,
        callers,
        callees,
        callee_depth=callee_depth,
        caller_depth=caller_depth,
    )

    # Map every symbol in scope to its source definition
    definitions = _fetch_definitions(scope, repo)

    # Assemble markdown, trimming if over budget
    return _render(target_key, definitions, scope, max_tokens)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_callers(graph: dict[str, list[str]]) -> dict[str, list[str]]:
    """Reverse the graph: callee -> list of callers."""
    rev: dict[str, list[str]] = {}
    for caller, callees in graph.items():
        for c in callees:
            rev.setdefault(c, []).append(caller)
    # Deduplicate
    return {k: list(dict.fromkeys(v)) for k, v in rev.items()}


def _resolve_target(target: str, keys: set[str]) -> str | None:
    """Find the exact key matching *target*, or a suffix match."""
    if target in keys:
        return target
    # Suffix match: "resolve" -> "resolver.resolve"
    suffix_hits = [k for k in keys if k.endswith(f".{target}") or k == target]
    if len(suffix_hits) == 1:
        return suffix_hits[0]
    return None


def _collect_scope(
    target: str,
    callers: dict[str, list[str]],
    callees: dict[str, list[str]],
    callee_depth: int,
    caller_depth: int,
) -> set[str]:
    """All symbols within the requested distance of *target*."""
    scope: set[str] = {target}

    # Downward (callees)
    frontier = {target}
    for _depth in range(callee_depth):
        next_frontier: set[str] = set()
        for node in frontier:
            for c in callees.get(node, []):
                if c not in scope:
                    next_frontier.add(c)
        scope |= next_frontier
        frontier = next_frontier
        if not frontier:
            break

    # Upward (callers)
    frontier = {target}
    for _depth in range(caller_depth):
        next_frontier = set()
        for node in frontier:
            for p in callers.get(node, []):
                if p not in scope:
                    next_frontier.add(p)
        scope |= next_frontier
        frontier = next_frontier
        if not frontier:
            break

    return scope


def _fetch_definitions(
    scope: set[str],
    repo: Path,
) -> dict[str, str]:
    """Map each symbol in *scope* to its AST-extracted definition string."""
    defs: dict[str, str] = {}
    # Walk every .py file once, build a mapping of qualified name -> source
    for py_file in sorted(repo.rglob("*.py")):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        module = _module_name(py_file, repo)
        defs.update(_extract_defs(tree, source, module, scope))
    return defs


def _module_name(py_file: Path, repo: Path) -> str:
    """Dotted module id relative to repo root, e.g. ``mini_tracer.walker``."""
    rel = py_file.relative_to(repo)
    parts = list(rel.with_suffix("").parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    return ".".join(parts)


def _extract_defs(
    tree: ast.AST,
    source: str,
    module: str,
    scope: set[str],
) -> dict[str, str]:
    """Pull top-level and method definitions that are in *scope*.

    Adds BOTH the qualified name (``module.name``) and the bare name
    to the output so lookups match whichever form the graph uses.
    """
    defs: dict[str, str] = {}
    lines = source.splitlines()

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            qname = f"{module}.{node.name}" if module else node.name
            if qname in scope or node.name in scope:
                end = getattr(node, "end_lineno", node.lineno)
                snippet = _slice(lines, node.lineno, end)
                defs[qname] = snippet
                defs[node.name] = snippet
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mq = f"{qname}.{item.name}"
                    bare = f"{node.name}.{item.name}"
                    if mq in scope or bare in scope:
                        end = getattr(item, "end_lineno", item.lineno)
                        snippet = _slice(lines, item.lineno, end)
                        defs[mq] = snippet
                        defs[bare] = snippet
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qname = f"{module}.{node.name}" if module else node.name
            if qname in scope or node.name in scope:
                end = getattr(node, "end_lineno", node.lineno)
                snippet = _slice(lines, node.lineno, end)
                defs[qname] = snippet
                defs[node.name] = snippet

    return defs


def _slice(lines: list[str], start: int, end: int) -> str:
    """1-indexed inclusive slice of source lines."""
    return "\n".join(lines[start - 1 : end])


# Rough token estimate: ~4 chars per token for English/Python code.
_CHAR_PER_TOKEN = 4


def _render(
    target: str,
    definitions: dict[str, str],
    scope: set[str],
    max_tokens: int,
) -> str:
    """Assemble markdown, trimming aggressively if over budget."""
    parts: list[str] = [f"## Target: `{target}`\n"]

    # Target definition always first
    if target in definitions:
        parts.append(f"```python\n{definitions[target]}\n```\n")
    else:
        parts.append("_(definition not found in scope)_\n")

    # Callees section
    callees = sorted(s for s in scope if s != target and target in s)
    if callees:
        parts.append("## Callees (downward)\n")
        for c in callees:
            if c in definitions:
                parts.append(f"### `{c}`\n")
                parts.append(f"```python\n{definitions[c]}\n```\n")
            else:
                parts.append(f"- `{c}`\n")

    # Callers section
    # Identify callers as those in scope that are NOT callees and NOT the target
    callee_set = set(callees)
    callers = sorted(s for s in scope if s != target and s not in callee_set)
    if callers:
        parts.append("## Callers (upward)\n")
        for p in callers:
            if p in definitions:
                parts.append(f"### `{p}`\n")
                parts.append(f"```python\n{definitions[p]}\n```\n")
            else:
                parts.append(f"- `{p}`\n")

    raw = "".join(parts)
    est_tokens = len(raw) // _CHAR_PER_TOKEN
    if est_tokens > max_tokens:
        # Trim: drop callees first, then callers, then truncate blocks
        raw = (
            f"## Target: `{target}`\n\n"
            f"_Context trimmed to ~{max_tokens} tokens.\n\n"
        )
        if target in definitions:
            head = definitions[target][: max_tokens * _CHAR_PER_TOKEN]
            raw += f"```python\n{head}\n```\n"
    return raw
