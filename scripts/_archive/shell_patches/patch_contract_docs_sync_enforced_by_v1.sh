#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: sync contract docs Enforced By sections from repo reality (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

bash -n "${BASH_SOURCE[0]}"

PATCHER="scripts/_patch_contract_docs_sync_enforced_by_v1.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" "${PATCHER}"

echo "OK"
