# AGENTS.md — Harness configuration (v0)

## Core principles

1. **Verification is the gatekeeper.** No code reaches main without passing every sensor layer. The verify harness is stricter than a human reviewer because it is deterministic and reproducible.
2. **Scoped filesystem access.** Touch only files declared in the card scope. If a file isn't listed, don't write to it. Preflight sensors check for scope violations.
3. **Test-first.** Every feature card must include runnable acceptance criteria (`pytest`, `ruff`, compile check). If there is no runnable check, the card cannot be auto-promoted.
4. **Minimal, focused edits.** Don't refactor code outside the card's scope. Don't fix style issues in files you didn't touch.
5. **Compose exploration in Python.** The `python` tool gives you a full REPL in the repo root. Walk, grep, filter, analyse — then `read_file` only what you need.

## How to run tests

```bash
# Always use uv — never bare python
uv run pytest tests/ -v --tb=short
uv run ruff check src/ tests/
```

## File placement

- Source modules: `src/mini_tracer/<module>.py`
- Tests: `tests/test_<module>.py`
- Fixtures: `tests/fixtures/<name>.py`
- All public symbols must have docstrings.

## Hard constraints

- Never emit built-in / stdlib names as call-graph edges.
- Never import across formatter boundaries (json, mermaid, dot are independent).
- Never add a dependency without justification.
- Keep modules under 200 LOC.
- `mini-tracer = mini_tracer.cli:main` is the CLI entry.

## When uncertain about architecture

Output a confidence score below 0.7 and halt. Do not guess and continue. The `unverified` sensor catches cards with no runnable checks — if you cannot write a test, the scope is unclear.

## Verify checklist (applied every promotion)

1. **Computational** — `pytest` green + `ruff` clean + compile check
2. **Structural** — file count within scope, module edges unchanged
3. **Semantic** — reviewer agent checks spec match against the card text
