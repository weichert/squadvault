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


NOTE_MISSING_FN = """note_missing() {
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


def main() -> int:
    root = _repo_root()
    path = root / TARGET
    if not path.exists():
        print(f"FATAL: missing {TARGET}", file=sys.stderr)
        return 2

    s = _read(path)
    lines = s.splitlines(True)

    # Ensure verbose toggle + allowlisted counter exist after ALLOWLIST=...
    allowlist_line = 'ALLOWLIST="scripts/patch_pair_allowlist_v1.txt"\n'
    try:
        idx_allow = lines.index(allowlist_line)
    except ValueError:
        print("FATAL: could not find ALLOWLIST assignment anchor.", file=sys.stderr)
        return 3

    want_toggle = [
        "\n",
        "# Verbosity: set SV_PATCH_PAIR_VERBOSE=1 to print allowlisted details.\n",
        'SV_PATCH_PAIR_VERBOSE="${SV_PATCH_PAIR_VERBOSE:-0}"\n',
        "allowlisted_count=0\n",
        "\n",
    ]

    # If not present nearby, insert immediately after ALLOWLIST line.
    window = "".join(lines[idx_allow : min(len(lines), idx_allow + 10)])
    if "SV_PATCH_PAIR_VERBOSE" not in window or "allowlisted_count" not in window:
        lines[idx_allow + 1 : idx_allow + 1] = want_toggle

    # Find note_missing() start
    start = None
    for i, line in enumerate(lines):
        if line == "note_missing() {\n":
            start = i
            break
    if start is None:
        print("FATAL: could not find note_missing() function start.", file=sys.stderr)
        return 4

    # Find the end of the function as the first line that is exactly "}\n" after start.
    end = None
    for j in range(start + 1, len(lines)):
        if lines[j] == "}\n":
            end = j
            break
    if end is None:
        print("FATAL: could not find note_missing() function closing brace.", file=sys.stderr)
        return 5

    # Replace block (inclusive) with our canonical function.
    new_block_lines = [ln + "\n" if not ln.endswith("\n") else ln for ln in NOTE_MISSING_FN.splitlines()]
    lines[start : end + 1] = new_block_lines

    # Remove any immediate stray "}" line(s) right after the function (the bug you hit).
    k = start + len(new_block_lines)
    removed = 0
    while k < len(lines) and lines[k].strip() == "}":
        del lines[k]
        removed += 1

    # Ensure the final OK line is the quiet/verbose-aware form.
    # If it's already patched, leave it. Otherwise replace the legacy single-line OK.
    joined = "".join(lines)
    if "allowlisted_count" in joined and "SV_PATCH_PAIR_VERBOSE" in joined:
        pass  # likely already adjusted; don't force.
    else:
        tail_old = 'echo "OK: patcher/wrapper pairing gate passed."\n'
        if tail_old in joined:
            tail_new = (
                'if [ "$allowlisted_count" -ne 0 ] && [ "${SV_PATCH_PAIR_VERBOSE}" != "1" ]; then\n'
                '  echo "OK: patcher/wrapper pairing gate passed. (allowlisted missing pairs: ${allowlisted_count}; suppressed; set SV_PATCH_PAIR_VERBOSE=1)"\n'
                "else\n"
                '  echo "OK: patcher/wrapper pairing gate passed."\n'
                "fi\n"
            )
            joined = joined.replace(tail_old, tail_new, 1)
            lines = joined.splitlines(True)

    out = "".join(lines)
    changed = _write_if_changed(path, out)
    if changed:
        extra = f" (removed stray braces: {removed})" if removed else ""
        print(f"OK: patch applied (v2) — note_missing normalized.{extra}")
    else:
        print("OK: no changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
