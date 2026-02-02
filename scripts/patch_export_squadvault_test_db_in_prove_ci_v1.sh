#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: export SQUADVAULT_TEST_DB in prove_ci.sh (v1) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/py" "$repo_root/scripts/_patch_export_squadvault_test_db_in_prove_ci_v1.py"

echo "==> bash -n: scripts/prove_ci.sh"
bash -n "$repo_root/scripts/prove_ci.sh"

echo "OK"
