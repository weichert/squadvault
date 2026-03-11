#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/.." && pwd)"

patcher="${repo_root}/scripts/_patch_prove_ci_add_creative_surface_registry_discoverability_gate_v1.py"
prove="${repo_root}/scripts/prove_ci.sh"

bash -n "$0"
"${repo_root}/scripts/py" -m py_compile "$patcher"
"${repo_root}/scripts/py" "$patcher"

needle="gate_creative_surface_registry_discoverability_v1.sh"
c="$(grep -n --fixed-strings "$needle" "$prove" | wc -l | tr -d ' ')"
test "$c" = "1"

bash -n "$prove"
