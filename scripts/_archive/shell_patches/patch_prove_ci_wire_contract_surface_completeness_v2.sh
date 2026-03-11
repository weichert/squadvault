#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire contract surface completeness proof into prove_ci (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

bash -n "${BASH_SOURCE[0]}"

PATCHER="scripts/_patch_prove_ci_wire_contract_surface_completeness_v2.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" "${PATCHER}"

bash -n scripts/prove_ci.sh

echo "OK"
