#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/ops_orchestrate.sh")

OLD = r'''echo
echo "=== Prove: scripts/prove_ci.sh ==="
./scripts/prove_ci.sh

if [[ "${commit_enabled}" == "1" ]]; then
  if [[ "${pass1_changed}" != "1" ]]; then
    die "--commit requested but no changes occurred"
  fi

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
  echo "==> commit OK"
else
  if [[ -n "$(git status --porcelain)" ]]; then
    die "tree not clean after successful run; use --commit or revert changes"
  fi
fi

echo
echo "=== Ops Orchestrator: OK ==="
'''

NEW = r'''if [[ "${commit_enabled}" == "1" ]]; then
  if [[ "${pass1_changed}" != "1" ]]; then
    die "--commit requested but no changes occurred"
  fi

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
  echo "==> commit OK"

  echo
  echo "=== Prove: scripts/prove_ci.sh ==="
  ./scripts/prove_ci.sh
else
  if [[ -n "$(git status --porcelain)" ]]; then
    die "tree not clean after successful run; use --commit or revert changes"
  fi

  echo
  echo "=== Prove: scripts/prove_ci.sh ==="
  ./scripts/prove_ci.sh
fi

echo
echo "=== Ops Orchestrator: OK ==="
'''

def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if NEW in text:
        print("OK: ops_orchestrate already commits before prove when --commit (v1).")
        return
    if OLD not in text:
        raise SystemExit("ERROR: could not locate expected prove/commit block in scripts/ops_orchestrate.sh")
    TARGET.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print("OK: patched ops_orchestrate to commit before prove when --commit (v1).")

if __name__ == "__main__":
    main()
