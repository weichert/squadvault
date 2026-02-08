from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/gate_ops_indices_no_autofill_placeholders_v1.sh")

# Canonical gate text (exactly what we want in-repo)
GATE_TEXT = r"""#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: Ops indices must not contain autofill placeholders (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

needle="— (autofill) describe gate purpose"
root="docs/80_indices/ops"

if grep -nR -- "${needle}" "${root}" >/dev/null; then
  echo "ERROR: found autofill placeholders in ${root}:"
  grep -nR -- "${needle}" "${root}" || true
  exit 1
fi

echo "OK: no autofill placeholders found in ${root}"
"""

def _normalize(text: str) -> str:
    # Ensure the file always ends with exactly one trailing newline (stable diffs).
    if not text.endswith("\n"):
        text += "\n"
    return text

def main() -> None:
    desired = _normalize(GATE_TEXT)

    if GATE.exists():
        current = GATE.read_text(encoding="utf-8")
        if _normalize(current) == desired:
            print(f"OK: gate already up to date: {GATE}")
            return

    # Write canonical text
    GATE.write_text(desired, encoding="utf-8")
    print("UPDATED:", GATE)

if __name__ == "__main__":
    main()
