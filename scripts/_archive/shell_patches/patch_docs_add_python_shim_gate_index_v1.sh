#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: docs add python shim gate index (v1) ==="

./scripts/py scripts/_patch_docs_add_python_shim_gate_index_v1.py

echo "==> bash -n wrapper"
bash -n scripts/patch_docs_add_python_shim_gate_index_v1.sh

echo "==> confirm doc header"
sed -n '1,25p' docs/80_indices/ops/CI_Python_Shim_Compliance_Gate_v1.0.md

echo "==> confirm index link"
grep -n "CI Python Shim Compliance Gate" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true

echo "OK"
