#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PATCHER="scripts/_patch_wire_creative_surface_registry_parity_gate_v1.py"

./scripts/py -m py_compile "$PATCHER"
./scripts/py "$PATCHER"

# Sanity: prove_ci invokes the gate
grep -n --fixed-string "bash scripts/gate_creative_surface_registry_parity_v1.sh" scripts/prove_ci.sh >/dev/null

# Sanity: ops index has the bullet
grep -n --fixed-string "gate_creative_surface_registry_parity_v1.sh" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null

bash -n "$0"
echo "OK: patch_wire_creative_surface_registry_parity_gate_v1"
