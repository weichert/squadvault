#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: register CI creative sharepack proof runner in CI proof surface registry (v1) ==="

python -m py_compile scripts/_patch_ci_proof_surface_registry_add_ci_creative_sharepack_runner_v1.py
./scripts/py scripts/_patch_ci_proof_surface_registry_add_ci_creative_sharepack_runner_v1.py

echo "==> sanity: marker present"
grep -n "SV_CI_PROOF_CREATIVE_SHAREPACK_IF_AVAILABLE_v1" -n docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md

echo "OK"
