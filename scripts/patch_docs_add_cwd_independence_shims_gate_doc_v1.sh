#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: docs add CWD independence shims gate doc (v1) ==="

./scripts/py -m py_compile scripts/_patch_docs_add_cwd_independence_shims_gate_doc_v1.py
./scripts/py scripts/_patch_docs_add_cwd_independence_shims_gate_doc_v1.py

echo "==> bash -n wrapper"
bash -n scripts/patch_docs_add_cwd_independence_shims_gate_doc_v1.sh

echo "==> preview doc header"
sed -n '1,40p' docs/80_indices/ops/CI_CWD_Independence_Shims_Gate_v1.0.md

echo "==> confirm index link"
grep -n "CWD Independence Gate" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true

echo "OK"
