#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/.." && pwd)"

patcher="${repo_root}/scripts/_patch_fix_patch_index_creative_surface_registry_discoverability_wrapper_backticks_v1.py"
target="${repo_root}/scripts/patch_index_creative_surface_registry_discoverability_v1.sh"

bash -n "$0"
"${repo_root}/scripts/py" -m py_compile "$patcher"
"${repo_root}/scripts/py" "$patcher"

# Verify the escaped form exists exactly once
needle='snippet="\\`docs/80_indices/ops/Creative_Surface_Registry_v1.0.md\\`"'
c="$(grep -n --fixed-strings "$needle" "$target" | wc -l | tr -d ' ')"
test "$c" = "1"

# Wrapper itself must be valid bash
bash -n "$target"
