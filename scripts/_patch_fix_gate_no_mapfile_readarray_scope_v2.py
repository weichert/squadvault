from __future__ import annotations

from pathlib import Path
import re
import stat
import subprocess


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _clipwrite(rel_path: str, content: str) -> None:
    root = _repo_root()
    proc = subprocess.run(
        ["bash", str(root / "scripts" / "clipwrite.sh"), rel_path],
        input=content,
        text=True,
        cwd=str(root),
    )
    if proc.returncode != 0:
        raise SystemExit(f"ERROR: clipwrite failed for {rel_path} (exit {proc.returncode}).")


def _chmod_x(p: Path) -> None:
    mode = p.stat().st_mode
    p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


_GATE = r"""#!/usr/bin/env bash
set -euo pipefail

# === Gate: No mapfile/readarray in CI execution scripts/ (v1) ===
#
# macOS default bash is 3.2; mapfile/readarray are not available.
# Enforce only on CI execution surfaces (prove/gate/check), not patch wrappers or archives.
#
# Scope (tracked):
#   - scripts/prove_*.sh
#   - scripts/gate_*.sh
#   - scripts/check_*.sh
#
# Ignore:
#   - comment-only lines (after grep -n => "NN:# ...")
#   - this gate file itself (to avoid self-matches)

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SELF_DIR/.." && pwd)"
cd "$REPO_ROOT"

THIS="scripts/gate_no_mapfile_readarray_in_scripts_v1.sh"

fail=0
violations=""

while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ "$f" = "$THIS" ] && continue

  # ignore comment-only lines, but flag real usage
  if grep -nE '(^|[^A-Za-z0-9_])(mapfile|readarray)([^A-Za-z0-9_]|$)' "$f" \
      | grep -vE '^[0-9]+:[[:space:]]*#' >/dev/null; then
    violations+="$f:\n"
    violations+="$(grep -nE '(^|[^A-Za-z0-9_])(mapfile|readarray)([^A-Za-z0-9_]|$)' "$f" | grep -vE '^[0-9]+:[[:space:]]*#')\n"
    fail=1
  fi
done < <(
  git ls-files \
    "scripts/prove_*.sh" \
    "scripts/gate_*.sh" \
    "scripts/check_*.sh"
)

if [ "$fail" -ne 0 ]; then
  echo "FAIL: forbidden bash4-only builtins found in tracked CI execution scripts (mapfile/readarray)."
  echo
  # shellcheck disable=SC2059
  printf "%b" "$violations"
  exit 1
fi

echo "OK: no mapfile/readarray found in tracked CI execution scripts (v1)."
"""


def _patch_gate_file() -> None:
    root = _repo_root()
    rel = "scripts/gate_no_mapfile_readarray_in_scripts_v1.sh"
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    desired = _GATE.rstrip() + "\n"
    cur = _read(p)
    if cur == desired:
        _chmod_x(p)
        print("OK: gate already canonical (noop).")
        return

    _clipwrite(rel, desired)
    _chmod_x(p)
    print("OK: updated gate scope to prove/gate/check + fixed comment-ignore (v1).")


def _patch_add_gate_patcher() -> None:
    root = _repo_root()
    rel = "scripts/_patch_add_gate_no_mapfile_readarray_in_scripts_v1.py"
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)

    m = re.search(r'(?s)(_GATE\s*=\s*r""")(.+?)(""")', s)
    if not m:
        raise SystemExit("ERROR: could not find _GATE raw string in add-gate patcher (unexpected format).")

    current_gate_body = m.group(2)
    desired_gate_body = _GATE

    if current_gate_body == desired_gate_body:
        print("OK: add-gate patcher already contains desired _GATE (noop).")
        return

    new_gate = "_GATE = r\"\"\"" + _GATE + "\"\"\""
    s2 = s[: m.start(1)] + new_gate + s[m.end(3) :]

    # If replacement somehow yields identical file, treat as NOOP (idempotence)
    if s2 == s:
        print("OK: add-gate patcher already updated (noop).")
        return

    _clipwrite(rel, s2)
    print("OK: updated add-gate patcher gate text to match new scope/ignore rules.")


def main() -> int:
    _patch_gate_file()
    _patch_add_gate_patcher()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
