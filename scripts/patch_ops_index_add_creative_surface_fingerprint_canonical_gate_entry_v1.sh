#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: ops index add creative surface fingerprint canonical gate entry (v1) ==="

./scripts/py -m py_compile scripts/_patch_ops_index_add_creative_surface_fingerprint_canonical_gate_entry_v1.py
./scripts/py scripts/_patch_ops_index_add_creative_surface_fingerprint_canonical_gate_entry_v1.py

grep -n "gate_creative_surface_fingerprint_canonical_v1.sh" -n docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "OK"
