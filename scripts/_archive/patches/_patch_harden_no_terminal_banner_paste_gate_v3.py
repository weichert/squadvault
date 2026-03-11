from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/gate_no_terminal_banner_paste_v1.sh")

NEW_TEXT = """#!/usr/bin/env bash
# SquadVault — gate: no pasted terminal banners (v1)
#
# Purpose:
#   Fail if any tracked scripts contain pasted terminal login/banner noise.
#
# Escape hatch:
#   SV_ALLOW_TERMINAL_BANNER_PASTE=1
#     -> WARN, skip enforcement, exit 0
#
# Determinism / Safety:
#   - repo-root anchored
#   - git grep only (tracked files)
#   - restricted to likely text file types via pathspecs
#   - no xargs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ "${SV_ALLOW_TERMINAL_BANNER_PASTE:-0}" == "1" ]]; then
  echo "WARN: SV_ALLOW_TERMINAL_BANNER_PASTE=1 set — skipping terminal banner paste enforcement."
  exit 0
fi

# Restrict scanning to likely-text tracked files only.
# Use git pathspec glob-magic so the shell does not expand anything.
PATHSPECS=(
  ':(glob)scripts/**/*.sh'
  ':(glob)scripts/**/*.py'
  ':(glob)scripts/**/*.md'
  ':(glob)scripts/**/*.txt'
)

# High-signal banner patterns (anchored to start-of-line to avoid matching literals in code/comments).
# NOTE: Use ERE. Escape dots in URLs.
PATTERN='^(Last login:|The default interactive shell is now zsh\\.|To update your account to use zsh, please run `chsh -s|For more details, please visit https://support\\.apple\\.com/kb/HT208050\\.|Changing shell for|Password for|wtmp begins)'

echo "==> No terminal banner paste gate"

set +e
HITS="$(git grep -nE "${PATTERN}" -- "${PATHSPECS[@]}")"
rc=$?
set -e

# git grep exit codes:
#   0 = matches found
#   1 = no matches
#   2+ = error
if [[ $rc -ge 2 ]]; then
  echo "ERROR: git grep failed unexpectedly (rc=${rc})."
  exit $rc
fi

if [[ $rc -eq 0 ]]; then
  echo "ERROR: detected pasted terminal banner content in scripts/ (restricted file types)."
  echo
  echo "Offending lines:"
  echo "${HITS}"
  echo
  echo "Fix:"
  echo "  - Remove the pasted banner lines from the file(s)."
  echo "  - Re-run: bash scripts/gate_no_terminal_banner_paste_v1.sh"
  exit 1
fi

echo "OK: no pasted terminal banner content detected."
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: expected gate not found: {TARGET}")

    old = TARGET.read_text(encoding="utf-8")

    # Refuse to patch if this doesn't resemble the expected gate file.
    if "terminal banner" not in old and "No terminal banner paste gate" not in old and "Last login" not in old:
        raise SystemExit("ERROR: target does not appear to be the terminal banner gate; refusing to patch.")

    if old == NEW_TEXT:
        print("OK: gate already hardened (v3 patch is idempotent).")
        return

    TARGET.write_text(NEW_TEXT, encoding="utf-8")
    print("OK: wrote hardened gate content (v3) to scripts/gate_no_terminal_banner_paste_v1.sh")

if __name__ == "__main__":
    main()
