#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove stray prove_ci SQUADVAULT_TEST_DB rhs line (v3) ==="

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$self_dir/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_fix_prove_ci_remove_stray_test_db_rhs_v3.py

echo "==> bash -n scripts/prove_ci.sh"
bash -n scripts/prove_ci.sh

echo "OK"
