#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle v1 — Lock C (persist draft direct) v2 ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_rivalry_chronicle_v1_lock_c_persist_direct_v2.py

echo
echo "Next: rerun rivalry-chronicle, then query recap_artifacts for RIVALRY_CHRONICLE_V1."
