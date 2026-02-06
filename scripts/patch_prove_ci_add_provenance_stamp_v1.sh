#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci add provenance stamp (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_ci_add_provenance_stamp_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
echo "OK"
