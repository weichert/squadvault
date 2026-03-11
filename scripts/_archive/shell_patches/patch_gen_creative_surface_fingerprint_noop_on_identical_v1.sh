#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: creative surface fingerprint noop-on-identical (v1) ==="

echo "==> py_compile patcher"
./scripts/py -m py_compile scripts/_patch_gen_creative_surface_fingerprint_noop_on_identical_v1.py

echo "==> run patcher"
./scripts/py scripts/_patch_gen_creative_surface_fingerprint_noop_on_identical_v1.py

echo "==> sanity: run generator once"
./scripts/py scripts/gen_creative_surface_fingerprint_v1.py

echo "OK"
