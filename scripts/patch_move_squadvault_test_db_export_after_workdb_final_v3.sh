#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: move SQUADVAULT_TEST_DB export after WORK_DB final (v3) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/py" "$repo_root/scripts/_patch_move_squadvault_test_db_export_after_workdb_final_v3.py"

echo "==> bash -n: scripts/prove_ci.sh"
bash -n "$repo_root/scripts/prove_ci.sh"

echo "OK"
