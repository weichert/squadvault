#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

OPS = Path("scripts/ops_orchestrate.sh")

COMMIT_BLOCK = """\
if [[ "${commit_enabled}" == "1" ]]; then
  if [[ "${pass1_changed}" != "1" ]]; then
    echo "OK: --commit requested but no changes occurred (no-op); skipping commit"
  else
    echo
    echo "=== Commit (explicit) ==="
    git add -A
    if git diff --cached --quiet; then
      die "unexpected: nothing staged after git add -A"
    fi
    git commit -m "${commit_msg}"

    if [[ -n "$(git status --porcelain)" ]]; then
      die "post-commit tree not clean (unexpected)"
    fi
  fi
fi

"""

def find_line_idx(lines: list[str], start: int, predicates) -> int:
    for i in range(start, len(lines)):
        s = lines[i]
        for pred in predicates:
            if pred(s):
                return i
    return -1

def main() -> None:
    s = OPS.read_text(encoding="utf-8")
    lines = s.splitlines(True)

    # 1) find commit block start
    start_idx = find_line_idx(
        lines,
        0,
        predicates=[
            lambda x: 'if [[ "${commit_enabled}" == "1" ]]; then' in x,
            lambda x: "if [[ \"${commit_enabled}\" == \"1\" ]]; then" in x,
        ],
    )
    if start_idx < 0:
        raise SystemExit("ERROR: could not find commit_enabled block start")

    # 2) find "prove" anchor after the commit block
    prove_idx = find_line_idx(
        lines,
        start_idx + 1,
        predicates=[
            lambda x: "=== Prove:" in x,
            lambda x: "scripts/prove_ci.sh" in x,
            lambda x: "prove_ci.sh" in x and "echo" in x,
            lambda x: "prove_ci.sh" in x and ("./" in x or "bash " in x),
        ],
    )
    if prove_idx < 0:
        raise SystemExit("ERROR: could not find prove anchor after commit block (looked for '=== Prove:' or 'prove_ci.sh')")

    # Replace [start_idx : prove_idx) with COMMIT_BLOCK
    new_lines = []
    new_lines.extend(lines[:start_idx])
    new_lines.append(COMMIT_BLOCK)
    new_lines.extend(lines[prove_idx:])

    OPS.write_text("".join(new_lines), encoding="utf-8")
    print("OK: rewrote ops_orchestrate commit block safely (v6.3).")

if __name__ == "__main__":
    main()
