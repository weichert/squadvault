#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Fix recap_artifacts signature ordering (v2, full reorder) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_fix_recap_artifacts_signature_order_v2.py

echo
echo "Next:"
echo "  python -m py_compile src/squadvault/core/recaps/recap_artifacts.py"
