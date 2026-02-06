#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts draft creator honors artifact_type (v1) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_recap_artifacts_draft_creator_honor_artifact_type_v1.py

echo
echo "Compile check:"
python -m py_compile src/squadvault/core/recaps/recap_artifacts.py
echo "OK: compile"

echo
echo "Next: rerun rivalry-chronicle and verify recap_artifacts contains artifact_type=RIVALRY_CHRONICLE_V1."
