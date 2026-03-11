#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: add creative surface fingerprint canonical gate to prove_ci (v1) ==="

./scripts/py -m py_compile scripts/_patch_prove_ci_add_creative_surface_fingerprint_canonical_gate_v1.py
./scripts/py scripts/_patch_prove_ci_add_creative_surface_fingerprint_canonical_gate_v1.py

bash -n scripts/prove_ci.sh
grep -n "gate_creative_surface_fingerprint_canonical_v1.sh" -n scripts/prove_ci.sh

echo "OK"
