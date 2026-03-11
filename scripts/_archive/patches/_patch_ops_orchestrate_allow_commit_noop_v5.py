#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

OPS = Path("scripts/ops_orchestrate.sh")

START = 'if [[ "${commit_enabled}" == "1" ]]; then'
PROVE = '=== Prove: scripts/prove_ci.sh ==='

def main() -> None:
    s = OPS.read_text(encoding="utf-8")
    lines = s.splitlines(True)

    # Find start of commit block
    try:
        i0 = next(i for i, ln in enumerate(lines) if ln.rstrip("\n") == START)
    except StopIteration:
        raise SystemExit("ERROR: could not locate commit_enabled block start")

    # Find the prove section (end anchor)
    try:
        i_prove = next(i for i, ln in enumerate(lines) if PROVE in ln)
    except StopIteration:
        raise SystemExit("ERROR: could not locate prove section anchor")

    if i_prove <= i0:
        raise SystemExit("ERROR: prove anchor found before commit block")

    # Replace everything from START up to (but not including) the prove anchor.
    new_block = [
        'if [[ "${commit_enabled}" == "1" ]]; then\n',
        '  if [[ "${pass1_changed}" != "1" ]]; then\n',
        '    echo "OK: --commit requested but no changes occurred (no-op); skipping commit"\n',
        '  else\n',
        '\n',
        '    echo "=== Commit (explicit) ==="\n',
        '    git add -A\n',
        '    if git diff --cached --quiet; then\n',
        '      die "unexpected: nothing staged after git add -A"\n',
        '    fi\n',
        '    git commit -m "${commit_msg}"\n',
        '\n',
        '    if [[ -n "$(git status --porcelain)" ]]; then\n',
        '      die "post-commit tree not clean (unexpected)"\n',
        '    fi\n',
        '    echo "==> commit OK"\n',
        '  fi\n',
        'fi\n',
        '\n',
    ]

    out = "".join(lines[:i0] + new_block + lines[i_prove:])
    if out == s:
        print("OK: ops_orchestrate already has commit no-op semantics (v5 no-op).")
        return

    OPS.write_text(out, encoding="utf-8")
    print("OK: rewrote ops_orchestrate commit block (v5).")

if __name__ == "__main__":
    main()
