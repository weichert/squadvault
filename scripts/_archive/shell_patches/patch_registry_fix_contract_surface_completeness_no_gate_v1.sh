#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: registry must not list gate_contract_surface_completeness (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

bash -n "${BASH_SOURCE[0]}"

PATCHER="scripts/_patch_registry_fix_contract_surface_completeness_no_gate_v1.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" "${PATCHER}"

echo "OK"
