#!/usr/bin/env bash
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
