#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs CI indices — Golden Path ephemeral exports note (v1) ==="

python="${PYTHON:-python}"
$python scripts/_patch_docs_ci_indices_golden_path_ephemeral_exports_v1.py

echo "OK"
