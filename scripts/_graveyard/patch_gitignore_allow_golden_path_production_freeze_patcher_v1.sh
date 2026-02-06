#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: allowlist Golden Path production freeze patcher in .gitignore (v1) ==="
python="${PYTHON:-python}"
"$python" scripts/_patch_gitignore_allow_golden_path_production_freeze_patcher_v1.py

echo "==> git diff -- .gitignore (if any)"
git diff -- .gitignore || true

echo "OK"
