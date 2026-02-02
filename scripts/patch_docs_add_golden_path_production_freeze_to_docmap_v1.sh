#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Golden Path production freeze link to canonical doc map (v1) ==="
python="${PYTHON:-python}"
"$python" scripts/_patch_docs_add_golden_path_production_freeze_to_docmap_v1.py

echo "==> sanity: show Notes section"
# Print from Notes header to end-of-file (small file)
awk 'found{print} /^## Notes/{found=1; print}' docs/canonical/Documentation_Map_and_Canonical_References.md

echo "OK"
