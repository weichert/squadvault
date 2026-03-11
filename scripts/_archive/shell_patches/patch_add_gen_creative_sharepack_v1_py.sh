#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: add scripts/gen_creative_sharepack_v1.py (deterministic generator) ==="

python -m py_compile scripts/_patch_add_gen_creative_sharepack_v1_py.py
./scripts/py scripts/_patch_add_gen_creative_sharepack_v1_py.py

# Validate python compiles
python -m py_compile scripts/gen_creative_sharepack_v1.py

# Validate wrapper syntax
bash -n scripts/patch_add_gen_creative_sharepack_v1_py.sh

echo "OK"
