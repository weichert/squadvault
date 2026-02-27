from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PY_SHIM = REPO / "scripts" / "py"

CANON = """#!/usr/bin/env bash
set -euo pipefail

# scripts/py — canonical python shim (v1)
# Goals:
# - CWD-independent (safe under any working directory)
# - Deterministic tool selection (prefer python3, fallback to python)
# - Exec passthrough (propagate exit code)
repo_root="$(
  cd "$(dirname "$0")/.." >/dev/null 2>&1
  pwd
)"
cd "${repo_root}"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$@"
fi

echo "ERROR: python3/python not found on PATH" >&2
exit 127
"""

def main() -> None:
  old = PY_SHIM.read_text(encoding="utf-8") if PY_SHIM.exists() else ""
  if old != CANON:
    PY_SHIM.parent.mkdir(parents=True, exist_ok=True)
    PY_SHIM.write_text(CANON, encoding="utf-8")
    changed = True
  else:
    changed = False

  if PY_SHIM.exists():
    mode = PY_SHIM.stat().st_mode
    if (mode & 0o100) == 0:
      PY_SHIM.chmod(mode | 0o100)
      changed = True

  if changed:
    print("OK: restored scripts/py shim (v1)")
  else:
    print("OK: scripts/py shim already canonical (noop)")

if __name__ == "__main__":
  main()
