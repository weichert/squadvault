#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs CI indices — Golden Path NAC v3 + default DB note (v1) ==="

python="${PYTHON:-python}"
./scripts/py scripts/_patch_docs_ci_indices_golden_path_notes_v1.py

echo "OK"
