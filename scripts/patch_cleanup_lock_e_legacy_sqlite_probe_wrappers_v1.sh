#!/usr/bin/env bash
set -euo pipefail

echo "=== Cleanup: remove legacy Lock E sqlite probe wrapper scripts v1 ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

FILES=(
  scripts/patch_lock_e_apply_wrapper_sqlite_probe_fixup_v1.sh
  scripts/patch_lock_e_apply_wrapper_sqlite_probe_pretty_v1.sh
  scripts/patch_lock_e_apply_wrapper_sqlite_probe_pretty_v1b.sh
  scripts/patch_lock_e_apply_wrapper_sqlite_probe_pretty_v1c.sh
)

removed=0
for f in "${FILES[@]}"; do
  if [[ -f "$f" ]]; then
    rm -f "$f"
    echo "Removed: $f"
    removed=$((removed+1))
  else
    echo "OK: missing (already removed): $f"
  fi
done

echo
echo "Done. removed=$removed"
