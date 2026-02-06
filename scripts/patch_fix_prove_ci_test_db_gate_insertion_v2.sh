#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix prove_ci SQUADVAULT_TEST_DB gate insertion (v2) ==="

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$self_dir/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_fix_prove_ci_test_db_gate_insertion_v2.py

echo "==> bash -n scripts/prove_ci.sh"
bash -n scripts/prove_ci.sh

echo "OK"
