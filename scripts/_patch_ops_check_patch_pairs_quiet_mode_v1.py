from __future__ import annotations

from pathlib import Path
import subprocess
import sys


TARGET = Path("scripts/check_patch_pairs_v1.sh")


def _repo_root() -> Path:
    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    return Path(p)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_if_changed(p: Path, text: str) -> bool:
    if p.exists() and _read(p) == text:
        return False
    p.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    root = _repo_root()
    path = root / TARGET
    if not path.exists():
        print(f"FATAL: missing {TARGET}", file=sys.stderr)
        return 2

    s = _read(path)

    # Idempotency: if already patched, do nothing.
    if "SV_PATCH_PAIR_VERBOSE" in s and "allowlisted_count" in s:
        print("OK: no changes needed (quiet/verbose already present).")
        return 0

    # 1) Insert verbose toggle + allowlisted counter after ALLOWLIST=...
    needle = 'ALLOWLIST="scripts/patch_pair_allowlist_v1.txt"\n'
    if needle not in s:
        print("FATAL: could not find ALLOWLIST assignment anchor.", file=sys.stderr)
        return 3

    insert = (
        needle
        + "\n"
        + '# Verbosity: set SV_PATCH_PAIR_VERBOSE=1 to print allowlisted details.\n'
        + 'SV_PATCH_PAIR_VERBOSE="${SV_PATCH_PAIR_VERBOSE:-0}"\n'
        + 'allowlisted_count=0\n'
        + "\n"
    )
    s = s.replace(needle, insert, 1)

    # 2) Replace note_missing() to suppress allowlisted by default, but still count.
    old_fn_start = "note_missing() {\n"
    if old_fn_start not in s:
        print("FATAL: could not find note_missing() function anchor.", file=sys.stderr)
        return 4

    # Find the exact function block by simple markers.
    start = s.index(old_fn_start)
    end = s.find("}\n\n# Wrapper -> patcher", start)
    if end == -1:
        print("FATAL: could not locate end of note_missing() function.", file=sys.stderr)
        return 5

    new_fn = """note_missing() {
  local src="$1"
  local expected="$2"

  if is_allowlisted "$src"; then
    allowlisted_count=$((allowlisted_count + 1))
    if [ "${SV_PATCH_PAIR_VERBOSE}" = "1" ]; then
      echo "ALLOWLISTED: missing pair for $src"
      echo "            expected: $expected"
    fi
    return 0
  fi

  echo "ERROR: missing pair for $src"
  echo "       expected: $expected"
  missing_pairs=1
}
"""

    s = s[:start] + new_fn + s[end:]

    # 3) Adjust the final success line to mention suppressed allowlisted misses.
    tail_old = 'echo "OK: patcher/wrapper pairing gate passed."\n'
    tail_new = """if [ "$allowlisted_count" -ne 0 ] && [ "${SV_PATCH_PAIR_VERBOSE}" != "1" ]; then
  echo "OK: patcher/wrapper pairing gate passed. (allowlisted missing pairs: ${allowlisted_count}; suppressed; set SV_PATCH_PAIR_VERBOSE=1)"
else
  echo "OK: patcher/wrapper pairing gate passed."
fi
"""
    if tail_old not in s:
        print("FATAL: could not find final OK line anchor.", file=sys.stderr)
        return 6
    s = s.replace(tail_old, tail_new, 1)

    changed = _write_if_changed(path, s)
    print("OK: patch applied (quiet/verbose toggle added)." if changed else "OK: no changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
