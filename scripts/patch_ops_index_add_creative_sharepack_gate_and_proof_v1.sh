#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: ops index add creative sharepack gate + proof (v1) ==="

python -m py_compile scripts/_patch_ops_index_add_creative_sharepack_gate_and_proof_v1.py
./scripts/py scripts/_patch_ops_index_add_creative_sharepack_gate_and_proof_v1.py

bash -n scripts/patch_ops_index_add_creative_sharepack_gate_and_proof_v1.sh

echo "OK"
