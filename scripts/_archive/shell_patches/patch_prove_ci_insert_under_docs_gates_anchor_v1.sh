#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci insert a doc/index gate under docs_gates anchor (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# REQUIRED env vars:
#   SV_DOCS_GATES_INSERT_LABEL
#   SV_DOCS_GATES_INSERT_PATH
: "${SV_DOCS_GATES_INSERT_LABEL:?missing SV_DOCS_GATES_INSERT_LABEL}"
: "${SV_DOCS_GATES_INSERT_PATH:?missing SV_DOCS_GATES_INSERT_PATH}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_ci_insert_under_docs_gates_anchor_v1.py

echo "==> Verify: prove_ci now references the requested gate path"
grep -nF "bash ${SV_DOCS_GATES_INSERT_PATH}" scripts/prove_ci.sh >/dev/null

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/patch_prove_ci_insert_under_docs_gates_anchor_v1.sh

echo "OK"
