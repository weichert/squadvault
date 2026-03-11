#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: add scripts/prove_creative_sharepack_determinism_v1.sh ==="

python -m py_compile scripts/_patch_add_prove_creative_sharepack_determinism_v1_sh.py
./scripts/py scripts/_patch_add_prove_creative_sharepack_determinism_v1_sh.py

chmod +x scripts/prove_creative_sharepack_determinism_v1.sh

bash -n scripts/prove_creative_sharepack_determinism_v1.sh
bash -n scripts/patch_add_prove_creative_sharepack_determinism_v1_sh.sh

echo "OK"
