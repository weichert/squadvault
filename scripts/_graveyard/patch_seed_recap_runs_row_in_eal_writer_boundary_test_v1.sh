#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: seed recap_runs row in EAL writer boundary test (v1) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/py" "$repo_root/scripts/_patch_seed_recap_runs_row_in_eal_writer_boundary_test_v1.py"

echo "OK"
