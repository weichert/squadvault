#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/.." && pwd)"

index="${repo_root}/docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
marker="SV_CREATIVE_SURFACE_REGISTRY: v1"
bullet="docs/80_indices/ops/Creative_Surface_Registry_v1.0.md — Creative Surface Registry (canonical pointers) (v1)"

c_marker="$(grep -n --fixed-strings "$marker" "$index" | wc -l | tr -d ' ')"
c_bullet="$(grep -n --fixed-strings "$bullet" "$index" | wc -l | tr -d ' ')"

test "$c_marker" = "1"
test "$c_bullet" = "1"
