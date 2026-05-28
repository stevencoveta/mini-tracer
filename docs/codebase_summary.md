# mini-tracer Codebase

A small Python CLI that extracts static call graphs and emits them as JSON, Mermaid, or Graphviz DOT

---

## Module Overview

| Module | Purpose | Public Symbols |
|--------|---------|----------------|
| `__init__.py` | mini-tracer: static Python call graph extractor. | — |
| `cli.py` | argparse-based CLI entry point for mini-tracer. | main |
| `resolver.py` | Cross-file resolution: map names to qualified identifiers. | resolve_calls, walk_directory |
| `walker.py` | AST walk: collect function/method definitions and calls per file. | CallGraphVisitor, walk_file |
| `formats/__init__.py` | Output formatters for call graphs. | — |
| `formats/dot.py` | Graphviz DOT output format for call graphs. | format_dot |
| `formats/json_out.py` | JSON output format for call graphs. | format_json |
| `formats/mermaid.py` | Mermaid output format for call graphs. | format_mermaid |

---

| | __init__ | cli | resolver | walker | formats | dot | json_out | mermaid |
|---|---|---|---|---|---|---|---|---|
| __init__ |  |  |  |  |  |  |  |  |
| cli |  |  |  |  |  |  |  |  |
| resolver |  |  |  |  |  |  |  |  |
| walker |  |  |  |  |  |  |  |  |
| formats |  |  |  |  |  |  |  |  |
| dot |  |  |  |  |  |  |  |  |
| json_out |  |  |  |  |  |  |  |  |
| mermaid |  |  |  |  |  |  |  |  |

---

## mini_tracer

mini-tracer: static Python call graph extractor.

_(no public definitions)_

## cli

argparse-based CLI entry point for mini-tracer.

### `_build_graph(target)`

Build a call graph from a file or directory path.


### `main()`

Parse arguments, build the call graph, and emit the chosen format.


## resolver

Cross-file resolution: map names to qualified identifiers.

### `resolve_calls(calls, definitions, module_name)`

Resolve unqualified call names to qualified names.


### `_resolve_name(name, definitions, module_name, caller)`

Resolve a single name to its qualified form.


### `walk_directory(dirpath)`

Recursively walk a directory and extract all call graphs.


### `_path_to_module(filepath, basedir)`

Convert file path to module name.


## walker

AST walk: collect function/method definitions and calls per file.

### `walk_file(filepath)`

Parse a Python file and extract call graph.


### class `CallGraphVisitor`

Extract function/method definitions and their call sites.


### `CallGraphVisitor.__init__(self, calls, definitions)`

Initialize visitor with storage for calls and definitions.


### `CallGraphVisitor.visit_FunctionDef(self, node)`

Visit a function definition.


### `CallGraphVisitor.visit_AsyncFunctionDef(self, node)`

Visit an async function definition.


### `CallGraphVisitor.visit_ClassDef(self, node)`

Visit a class definition.


### `CallGraphVisitor.visit_Call(self, node)`

Visit a function call and record it.


### `CallGraphVisitor._extract_name(self, node)`

Extract a callable name from AST node.


## formats

Output formatters for call graphs.

_(no public definitions)_

## dot

Graphviz DOT output format for call graphs.

### `format_dot(calls)`

Format a call graph as Graphviz DOT.


## json_out

JSON output format for call graphs.

### `format_json(calls)`

Format a call graph as JSON.


## mermaid

Mermaid output format for call graphs.

### `format_mermaid(calls)`

Format a call graph as Mermaid graph TD syntax.


### `_sanitize_id(name)`

Convert a qualified name to a valid Mermaid node ID.

