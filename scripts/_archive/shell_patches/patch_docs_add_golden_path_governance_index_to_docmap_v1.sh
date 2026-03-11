#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Golden Path governance index link to canonical doc map (v1) ==="
python="${PYTHON:-python}"
./scripts/py scripts/_patch_docs_add_golden_path_governance_index_to_docmap_v1.py

echo "==> sanity: show Notes section"
awk 'found{print} /^## Notes/{found=1; print}' docs/canonical/Documentation_Map_and_Canonical_References.md

echo "OK"
