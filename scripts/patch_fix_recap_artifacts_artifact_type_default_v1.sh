#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Fix recap_artifacts artifact_type default (NameError) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_fix_recap_artifacts_artifact_type_default_v1.py

echo
echo "Next:"
echo "  python -m py_compile src/squadvault/core/recaps/recap_artifacts.py"
echo "  ./scripts/recap.sh rivalry-chronicle ..."
