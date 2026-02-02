#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Golden Path Production Freeze doc (v1) ==="

python="${PYTHON:-python}"
"$python" scripts/_patch_add_golden_path_production_freeze_v1.py

echo "==> sanity: show file header"
sed -n '1,40p' docs/canonical/Golden_Path_Production_Freeze_v1.0.md

echo "OK"
