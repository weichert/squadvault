#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: wire creative sharepack determinism into prove_ci (conditional, v3) ==="

python -m py_compile scripts/_patch_prove_ci_wire_creative_sharepack_determinism_if_available_v3.py
./scripts/py scripts/_patch_prove_ci_wire_creative_sharepack_determinism_if_available_v3.py

bash -n scripts/prove_ci.sh
bash -n scripts/patch_prove_ci_wire_creative_sharepack_determinism_if_available_v3.sh

echo "OK"
