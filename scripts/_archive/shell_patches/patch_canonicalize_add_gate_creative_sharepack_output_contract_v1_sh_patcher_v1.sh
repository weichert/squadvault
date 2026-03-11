#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: canonicalize add-gate creative sharepack patcher (v1) ==="

python -m py_compile scripts/_patch_canonicalize_add_gate_creative_sharepack_output_contract_v1_sh_patcher_v1.py
./scripts/py scripts/_patch_canonicalize_add_gate_creative_sharepack_output_contract_v1_sh_patcher_v1.py

python -m py_compile scripts/_patch_add_gate_creative_sharepack_output_contract_v1_sh.py
bash -n scripts/patch_add_gate_creative_sharepack_output_contract_v1_sh.sh

echo "OK"
