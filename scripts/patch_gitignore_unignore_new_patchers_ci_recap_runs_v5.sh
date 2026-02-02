#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: .gitignore unignore recap_runs patchers (v5) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/py" "$repo_root/scripts/_patch_gitignore_unignore_new_patchers_ci_recap_runs_v5.py"

echo "OK"
