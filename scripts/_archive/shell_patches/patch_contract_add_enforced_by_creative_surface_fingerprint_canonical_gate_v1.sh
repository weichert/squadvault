#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: contract add enforced-by creative surface fingerprint canonical gate (v1) ==="

./scripts/py -m py_compile scripts/_patch_contract_add_enforced_by_creative_surface_fingerprint_canonical_gate_v1.py
./scripts/py scripts/_patch_contract_add_enforced_by_creative_surface_fingerprint_canonical_gate_v1.py

grep -n "gate_creative_surface_fingerprint_canonical_v1.sh" -n docs/contracts/creative_sharepack_output_contract_v1.md

echo "OK"
