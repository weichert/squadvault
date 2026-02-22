#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/.." && pwd)"

patcher="${repo_root}/scripts/_patch_index_creative_surface_registry_discoverability_v1.py"
index="${repo_root}/docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

bash -n "$0"
"${repo_root}/scripts/py" -m py_compile "$patcher"
"${repo_root}/scripts/py" "$patcher"

marker="SV_CREATIVE_SURFACE_REGISTRY: v1"
bullet="docs/80_indices/ops/Creative_Surface_Registry_v1.0.md — Creative Surface Registry (canonical pointers) (v1)"

c_marker="$(grep -n --fixed-strings "$marker" "$index" | wc -l | tr -d ' ')"
c_bullet="$(grep -n --fixed-strings "$bullet" "$index" | wc -l | tr -d ' ')"
test "$c_marker" = "1"
test "$c_bullet" = "1"

# The old backticked doc snippet must be <= 1 now
snippet="\`docs/80_indices/ops/Creative_Surface_Registry_v1.0.md\`"
c_snip="$(grep -n --fixed-strings "$snippet" "$index" | wc -l | tr -d ' ')"
test "$c_snip" -le "1"

# Parity gate bullet should be exactly once now (it was duplicated)
par="scripts/gate_creative_surface_registry_parity_v1.sh — Creative Surface Registry parity gate (v1)"
c_par="$(grep -n --fixed-strings "$par" "$index" | wc -l | tr -d ' ')"
test "$c_par" = "1"
