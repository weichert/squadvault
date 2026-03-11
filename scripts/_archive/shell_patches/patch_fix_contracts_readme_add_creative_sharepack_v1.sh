#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: fix contracts README (add creative sharepack contract under Contract Documents) ==="

python -m py_compile scripts/_patch_fix_contracts_readme_add_creative_sharepack_v1.py
./scripts/py scripts/_patch_fix_contracts_readme_add_creative_sharepack_v1.py

# Validate wrapper syntax
bash -n scripts/patch_fix_contracts_readme_add_creative_sharepack_v1.sh

echo "OK"
