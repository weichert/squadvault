from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/gate_no_double_scripts_prefix_v2.sh")

EXPECTED = """#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: no double scripts prefix (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Scan the most regression-prone bash entrypoints:
# - prove scripts
# - gate scripts
# - patch wrappers
#
# bash3-safe: avoid mapfile; rely on git ls-files and a while/read loop.

scan_globs=(
  "scripts/prove_*.sh"
  "scripts/gate_*.sh"
  "scripts/patch_*.sh"
)

bad=0

for g in "${scan_globs[@]}"; do
  # If a glob matches nothing in git, git ls-files returns empty; that's OK.
  git ls-files "${g}" | while IFS= read -r f; do
    if [[ -z "${f}" ]]; then
      continue
    fi
    test -f "${f}"
    if grep -nF "scripts/scripts/" "${f}" >/dev/null; then
      echo "ERROR: detected forbidden 'scripts/scripts/' in ${f}"
      grep -nF "scripts/scripts/" "${f}" || true
      bad=1
    fi
  done
done

# NOTE: 'bad' set in a subshell when using a pipeline; enforce via a second pass.
# We re-check deterministically without relying on shell variable propagation.

found_any=0
for g in "${scan_globs[@]}"; do
  while IFS= read -r f; do
    if [[ -z "${f}" ]]; then
      continue
    fi
    if grep -nF "scripts/scripts/" "${f}" >/dev/null; then
      found_any=1
    fi
  done < <(git ls-files "${g}")
done

if [[ "${found_any}" -ne 0 ]]; then
  exit 1
fi

echo "OK: no 'scripts/scripts/' found in scanned scripts."
"""
def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")

def main() -> None:
    if TARGET.exists():
        existing = _read(TARGET)
        if existing != EXPECTED and existing != (EXPECTED + "\n"):
            _refuse(f"{TARGET} exists but does not match expected canonical contents.")
        return
    _write(TARGET, EXPECTED)

if __name__ == "__main__":
    main()
