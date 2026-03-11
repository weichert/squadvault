#!/usr/bin/env bash
set -euo pipefail
bash -n "$0"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python -m py_compile scripts/_patch_add_gate_creative_surface_registry_usage_v1.py
python scripts/_patch_add_gate_creative_surface_registry_usage_v1.py

# Verify via grep (fail-closed)
test -f scripts/gate_creative_surface_registry_usage_v1.sh
grep -n "gate_creative_surface_registry_usage_v1.sh" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null
grep -n "Gate: Creative Surface registry usage" scripts/prove_ci.sh >/dev/null

bash -n scripts/gate_creative_surface_registry_usage_v1.sh
