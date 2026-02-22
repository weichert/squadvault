#!/usr/bin/env bash
set -euo pipefail

# === Gate: No mapfile/readarray in scripts/ (v1) ===
#
# macOS default bash is 3.2; mapfile/readarray are not available.
# Static enforcement only: scan tracked scripts/*.sh for forbidden tokens.

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SELF_DIR/.." && pwd)"
cd "$REPO_ROOT"

fail=0
violations=""

while IFS= read -r f; do
  [ -z "$f" ] && continue

  if grep -nE '(^|[^A-Za-z0-9_])(mapfile|readarray)([^A-Za-z0-9_]|$)' "$f" >/dev/null; then
    violations+="$f:\n"
    violations+="$(grep -nE '(^|[^A-Za-z0-9_])(mapfile|readarray)([^A-Za-z0-9_]|$)' "$f")\n"
    fail=1
  fi
done < <(git ls-files "scripts/*.sh")

if [ "$fail" -ne 0 ]; then
  echo "FAIL: forbidden bash4-only builtins found in tracked scripts/*.sh (mapfile/readarray)."
  echo
  # shellcheck disable=SC2059
  printf "%b" "$violations"
  exit 1
fi

echo "OK: no mapfile/readarray found in tracked scripts/*.sh (v1)."
