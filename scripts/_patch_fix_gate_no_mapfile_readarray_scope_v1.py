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

# === Gate: No mapfile/readarray in active scripts/ (v1) ===
#
# macOS default bash is 3.2; mapfile/readarray are not available.
# Enforce only on ACTIVE tracked scripts surfaces, not archives.
#
# Scope:
#   - include: scripts/*.sh (tracked)
#   - exclude: scripts/_retired/**, scripts/_graveyard/**
# Ignore:
#   - comment-only lines (leading '#')
#   - this gate file itself (to avoid self-matches)

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SELF_DIR/.." && pwd)"
cd "$REPO_ROOT"

THIS="scripts/gate_no_mapfile_readarray_in_scripts_v1.sh"

fail=0
violations=""

while IFS= read -r f; do
  [ -z "$f" ] && continue

  case "$f" in
    scripts/_retired/*|scripts/_graveyard/*) continue ;;
  esac

  [ "$f" = "$THIS" ] && continue

  # ignore comment-only lines, but flag real usage
  if grep -nE '(^|[^A-Za-z0-9_])(mapfile|readarray)([^A-Za-z0-9_]|$)' "$f" \
      | grep -vE '^[[:space:]]*#' >/dev/null; then
    violations+="$f:\n"
    violations+="$(grep -nE '(^|[^A-Za-z0-9_])(mapfile|readarray)([^A-Za-z0-9_]|$)' "$f" | grep -vE '^[[:space:]]*#')\n"
    fail=1
  fi
done < <(git ls-files "scripts/*.sh")

if [ "$fail" -ne 0 ]; then
  echo "FAIL: forbidden bash4-only builtins found in ACTIVE tracked scripts/*.sh (mapfile/readarray)."
  echo
  # shellcheck disable=SC2059
  printf "%b" "$violations"
  exit 1
fi

echo "OK: no mapfile/readarray found in ACTIVE tracked scripts/*.sh (v1)."
"""


def _patch_gate_file() -> None:
    root = _repo_root()
    rel = "scripts/gate_no_mapfile_readarray_in_scripts_v1.sh"
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    desired = _GATE.rstrip() + "\n"
    if _read(p) == desired:
        _chmod_x(p)
        print("OK: gate already canonical (noop).")
        return

    _clipwrite(rel, desired)
    _chmod_x(p)
    print("OK: updated gate scope/ignore rules (v1).")


def _patch_add_gate_patcher() -> None:
    root = _repo_root()
    rel = "scripts/_patch_add_gate_no_mapfile_readarray_in_scripts_v1.py"
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)
    if "Gate: No mapfile/readarray in active scripts/" in s:
        print("OK: add-gate patcher already contains updated gate text (noop).")
        return

    # Replace the raw gate string assignment block conservatively.
    # We anchor on `_GATE = r"""` and the closing triple-quote.
    m = re.search(r'(?s)(_GATE\s*=\s*r""")(.+?)(""")', s)
    if not m:
        raise SystemExit("ERROR: could not find _GATE raw string in add-gate patcher (unexpected format).")

    new_gate = "_GATE = r\"\"\"" + _GATE + "\"\"\""
    s2 = s[: m.start(1)] + new_gate + s[m.end(3) :]
    if s2 == s:
        raise SystemExit("ERROR: failed to update add-gate patcher gate text (no change).")

    _clipwrite(rel, s2)
    print("OK: updated add-gate patcher gate text to match new scope/ignore rules.")


def main() -> int:
    _patch_gate_file()
    _patch_add_gate_patcher()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
