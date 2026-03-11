#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/.." && pwd)"

patcher="${repo_root}/scripts/_patch_ci_guardrails_index_add_creative_surface_registry_discoverability_gate_v1.py"
index="${repo_root}/docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

bash -n "$0"
"${repo_root}/scripts/py" -m py_compile "$patcher"
"${repo_root}/scripts/py" "$patcher"

needle="scripts/gate_creative_surface_registry_discoverability_v1.sh"
c="$(grep -n --fixed-strings "$needle" "$index" | wc -l | tr -d ' ')"
test "$c" = "1"
