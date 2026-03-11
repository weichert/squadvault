#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: .gitignore unignore new patchers (ci db fix) (v2) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/py" "$repo_root/scripts/_patch_gitignore_unignore_new_patchers_ci_db_fix_v2.py"

echo "OK"
