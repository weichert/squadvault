#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: add scripts/gate_creative_sharepack_output_contract_v1.sh ==="

python -m py_compile scripts/_patch_add_gate_creative_sharepack_output_contract_v1_sh.py
./scripts/py scripts/_patch_add_gate_creative_sharepack_output_contract_v1_sh.py

chmod +x scripts/gate_creative_sharepack_output_contract_v1.sh

bash -n scripts/gate_creative_sharepack_output_contract_v1.sh
bash -n scripts/patch_add_gate_creative_sharepack_output_contract_v1_sh.sh

echo "OK"
