#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: allowlist new patchers in .gitignore (v1) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/py" "$repo_root/scripts/_patch_allowlist_new_patchers_for_ci_db_fix_v1.py"

echo "OK"
