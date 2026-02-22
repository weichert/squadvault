#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/.." && pwd)"

patcher="${repo_root}/scripts/_patch_prove_ci_fix_creative_surface_registry_discoverability_repo_root_var_v1.py"
prove="${repo_root}/scripts/prove_ci.sh"

bash -n "$0"
"${repo_root}/scripts/py" -m py_compile "$patcher"
"${repo_root}/scripts/py" "$patcher"

needle='bash "${repo_root_for_gate}/scripts/gate_creative_surface_registry_discoverability_v1.sh"'
c="$(grep -n --fixed-strings "$needle" "$prove" | wc -l | tr -d ' ')"
test "$c" = "1"

old='bash "${repo_root}/scripts/gate_creative_surface_registry_discoverability_v1.sh"'
c_old="$(grep -n --fixed-strings "$old" "$prove" | wc -l | tr -d ' ')"
test "$c_old" = "0"

bash -n "$prove"
