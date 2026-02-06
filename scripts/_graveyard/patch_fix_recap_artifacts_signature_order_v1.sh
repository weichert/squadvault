#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Fix recap_artifacts create_recap_artifact_draft_idempotent arg order (v1) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_fix_recap_artifacts_signature_order_v1.py

echo
echo "Next: python -m py_compile src/squadvault/core/recaps/recap_artifacts.py"
echo "Then: rerun ./scripts/recap.sh rivalry-chronicle ..."
