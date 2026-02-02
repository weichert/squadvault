#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add ops index doc for Golden Path pytest pinning (v1) ==="
python="${PYTHON:-python}"

"$python" scripts/_patch_docs_add_golden_path_pytest_pinning_index_v1.py

echo "==> verify doc exists"
test -f docs/80_indices/ops/Golden_Path_Pytest_Pinning_v1.0.md
echo "OK"
