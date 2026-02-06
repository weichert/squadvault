#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix apply Lock E wrapper (unexpected EOF) v1 ==="

# Always run from repo root relative to this script, not caller CWD
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

./scripts/py scripts/_patch_fix_apply_lock_e_wrapper_unexpected_eof_v1.py

echo
echo "== Verify: bash -n =="
bash -n scripts/patch_apply_lock_e_final_state.sh
echo "OK: bash -n clean"

echo
echo "== Verify: normal execution (no SV_DB_PATH) =="
bash scripts/patch_apply_lock_e_final_state.sh
echo "OK: normal execution"

echo
echo "== Verify: sqlite sanity probe (SV_DB_PATH) =="
# If user hasn't set SV_DB_PATH externally, try the conventional local db name.
DB_DEFAULT=".local_squadvault.sqlite"
if [[ -z "${SV_DB_PATH:-}" ]]; then
  if [[ -f "$DB_DEFAULT" ]]; then
    SV_DB_PATH="$DB_DEFAULT" bash scripts/patch_apply_lock_e_final_state.sh
    echo "OK: SV_DB_PATH probe (default db) executed"
  else
    echo "NOTE: SV_DB_PATH not set and $DB_DEFAULT not found; skipping probe execution."
    echo "      To test: SV_DB_PATH=/path/to/db.sqlite bash scripts/patch_apply_lock_e_final_state.sh"
  fi
else
  SV_DB_PATH="$SV_DB_PATH" bash scripts/patch_apply_lock_e_final_state.sh
  echo "OK: SV_DB_PATH probe executed"
fi
