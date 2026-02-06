#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: tidy .gitignore allowlist placement for Golden Path production freeze patcher (v2) ==="
python="${PYTHON:-python}"
"$python" scripts/_patch_gitignore_allow_golden_path_production_freeze_patcher_v2.py

echo "==> git diff -- .gitignore (if any)"
git diff -- .gitignore || true

echo "OK"
