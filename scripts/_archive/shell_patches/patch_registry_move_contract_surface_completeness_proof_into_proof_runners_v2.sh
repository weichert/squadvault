#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: move contract surface completeness proof into Proof Runners list (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

bash -n "${BASH_SOURCE[0]}"

PATCHER="scripts/_patch_registry_move_contract_surface_completeness_proof_into_proof_runners_v2.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" "${PATCHER}"

echo "OK"
