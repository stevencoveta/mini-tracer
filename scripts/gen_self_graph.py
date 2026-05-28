"""Generate docs/self_graph.json by running mini-tracer on its own source."""

import json
import os
import subprocess
import sys


def main() -> None:
    """Invoke the mini-tracer CLI on src/mini_tracer/ and write docs/self_graph.json."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_target = os.path.join(repo_root, "src", "mini_tracer")
    out_path = os.path.join(repo_root, "docs", "self_graph.json")

    result = subprocess.run(
        [sys.executable, "-m", "mini_tracer.cli", src_target, "--format", "json"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    # Validate output is JSON with at least one key
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"error: CLI output is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict) or len(data) == 0:
        print("error: self-graph JSON is empty or not a dict", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(result.stdout)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
