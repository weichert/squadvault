#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: add Creative Surface Registry (v1.0) ==="

python -m py_compile scripts/_patch_add_creative_surface_registry_v1_0.py
./scripts/py scripts/_patch_add_creative_surface_registry_v1_0.py

bash -n scripts/patch_add_creative_surface_registry_v1_0.sh

echo "OK"
