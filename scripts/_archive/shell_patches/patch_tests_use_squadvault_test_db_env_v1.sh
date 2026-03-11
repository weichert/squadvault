#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: tests use SQUADVAULT_TEST_DB env var (v1) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/py" "$repo_root/scripts/_patch_tests_use_squadvault_test_db_env_v1.py"

echo "OK"
