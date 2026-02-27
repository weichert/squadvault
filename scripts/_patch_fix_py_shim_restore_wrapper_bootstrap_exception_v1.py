from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

WRAPPER = REPO / "scripts" / "patch_restore_scripts_py_shim_v1.sh"
GATE = REPO / "scripts" / "check_python_shim_compliance_v2.sh"

WRAPPER_CANON = """#!/usr/bin/env bash
set -euo pipefail

# patch_restore_scripts_py_shim_v1
# Idempotent wrapper: safe to run twice from clean.
#
# NOTE (bootstrap exception):
# This wrapper may need to run when scripts/py is missing or empty.
# In that case, it bootstraps via python3/python exactly once to restore scripts/py,
# then subsequent runs use ./scripts/py normally.

repo_root="$(
  cd "$(dirname "$0")/.." >/dev/null 2>&1
  pwd
)"
cd "${repo_root}"

# If scripts/py exists and is non-empty, use it (canonical path).
if [[ -s "./scripts/py" ]]; then
  ./scripts/py scripts/_patch_restore_scripts_py_shim_v1.py
  exit 0
fi

# Bootstrap only when scripts/py is missing/empty.
if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/_patch_restore_scripts_py_shim_v1.py
fi
if command -v python >/dev/null 2>&1; then
  exec python scripts/_patch_restore_scripts_py_shim_v1.py
fi

echo "ERROR: cannot bootstrap scripts/py — python3/python not found" >&2
exit 127
"""

def _read(p: Path) -> str:
  return p.read_text(encoding="utf-8")

def _write_if_changed(p: Path, s: str) -> bool:
  old = _read(p) if p.exists() else ""
  if old == s:
    return False
  p.parent.mkdir(parents=True, exist_ok=True)
  p.write_text(s, encoding="utf-8")
  return True

def main() -> None:
  if not WRAPPER.exists():
    raise SystemExit(f"ERROR: missing {WRAPPER}")
  if not GATE.exists():
    raise SystemExit(f"ERROR: missing {GATE}")

  changed = False

  # 1) Canonicalize wrapper content
  changed |= _write_if_changed(WRAPPER, WRAPPER_CANON)

  # 2) Add a narrow allowlist exception for this bootstrap wrapper in shim compliance gate (v2)
  gate_txt = _read(GATE)
  needle = "patch_restore_scripts_py_shim_v1.sh"
  if needle in gate_txt:
    pass
  else:
    # Insert into any existing allowlist/exceptions block if present; otherwise append a tiny block.
    marker_begin = "# SV_PY_SHIM_COMPLIANCE_EXCEPTIONS_v1_BEGIN"
    marker_end = "# SV_PY_SHIM_COMPLIANCE_EXCEPTIONS_v1_END"
    line = '  "scripts/patch_restore_scripts_py_shim_v1.sh" \\\n'

    if marker_begin in gate_txt and marker_end in gate_txt:
      pre, rest = gate_txt.split(marker_begin, 1)
      mid, post = rest.split(marker_end, 1)
      if line.strip() not in mid:
        mid2 = mid + line
        gate_txt = pre + marker_begin + mid2 + marker_end + post
        changed = True
    else:
      block = (
        "\n"
        f"{marker_begin}\n"
        "# Bootstrap exceptions (narrow; explicit)\n"
        "# - This wrapper exists to restore scripts/py when missing/empty.\n"
        f"{line}"
        f"{marker_end}\n"
      )
      gate_txt = gate_txt + block
      changed = True

    if changed:
      GATE.write_text(gate_txt, encoding="utf-8")

  if changed:
    print("OK: patched py shim restore wrapper + compliance exception (v1)")
  else:
    print("OK: py shim restore wrapper + compliance exception already canonical (noop)")

if __name__ == "__main__":
  main()
