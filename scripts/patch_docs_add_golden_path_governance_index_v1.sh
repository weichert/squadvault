#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Golden Path governance index doc (v1) ==="
python="${PYTHON:-python}"
./scripts/py scripts/_patch_docs_add_golden_path_governance_index_v1.py

echo "==> sanity: show file header"
sed -n '1,120p' docs/80_indices/ops/Golden_Path_Governance_Index_v1.0.md

echo "OK"
