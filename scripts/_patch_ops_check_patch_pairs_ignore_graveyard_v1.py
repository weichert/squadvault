from __future__ import annotations

from pathlib import Path
import subprocess
import sys

TARGET = Path("scripts/check_patch_pairs_v1.sh")

def repo_root() -> Path:
    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    return Path(p)

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write_if_changed(p: Path, s: str) -> bool:
    old = read_text(p) if p.exists() else None
    if old == s:
        return False
    p.write_text(s, encoding="utf-8")
    return True

def main() -> int:
    root = repo_root()
    path = root / TARGET
    if not path.exists():
        print(f"FATAL: missing {TARGET}", file=sys.stderr)
        return 2

    s = read_text(path)

    # Idempotency: if already patched, exit clean.
    if "SV_PATCH_PAIR_IGNORE_GRAVEYARD" in s and "_graveyard" in s:
        print("OK: no changes needed (graveyard ignore already present).")
        return 0

    # Anchor: after allowlist assignment block we already have
    anchor = 'ALLOWLIST="scripts/patch_pair_allowlist_v1.txt"\n'
    if anchor not in s:
        print("FATAL: could not find ALLOWLIST assignment anchor.", file=sys.stderr)
        return 3

    insert = (
        anchor
        + "\n"
        + "# SV_PATCH_PAIR_IGNORE_GRAVEYARD_V1\n"
        + "# Ignore historical patch artifacts under scripts/_graveyard/ (not part of active tooling).\n"
        + 'SV_PATCH_PAIR_IGNORE_GRAVEYARD="${SV_PATCH_PAIR_IGNORE_GRAVEYARD:-1}"\n'
        + 'GRAVEYARD_PREFIX="scripts/_graveyard/"\n'
        + "\n"
    )
    s = s.replace(anchor, insert, 1)

    # Add a small helper to skip paths when ignore is on.
    helper_anchor = "is_allowlisted() {\n"
    idx = s.find(helper_anchor)
    if idx == -1:
        print("FATAL: could not find is_allowlisted() function anchor.", file=sys.stderr)
        return 4

    helper = """is_ignored_path() {
  local path="$1"
  if [ "${SV_PATCH_PAIR_IGNORE_GRAVEYARD}" = "1" ]; then
    case "$path" in
      ${GRAVEYARD_PREFIX}*) return 0 ;;
    esac
  fi
  return 1
}

"""
    # Insert helper immediately before is_allowlisted()
    s = s[:idx] + helper + s[idx:]

    # Update wrapper loop: skip ignored
    needle1 = '    [ -z "$w" ] && continue\n'
    if needle1 not in s:
        print("FATAL: could not find wrapper loop continue anchor.", file=sys.stderr)
        return 5
    s = s.replace(needle1, needle1 + '    is_ignored_path "$w" && continue\n', 1)

    # Update patcher loop: skip ignored
    needle2 = '    [ -z "$p" ] && continue\n'
    if needle2 not in s:
        print("FATAL: could not find patcher loop continue anchor.", file=sys.stderr)
        return 6
    s = s.replace(needle2, needle2 + '    is_ignored_path "$p" && continue\n', 1)

    changed = write_if_changed(path, s)
    print("OK: patch applied (ignore graveyard v1)." if changed else "OK: no changes needed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
