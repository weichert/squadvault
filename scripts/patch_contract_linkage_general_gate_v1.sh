#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: general contract linkage gate + RC wrapper delegation (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

PATCHER="scripts/_patch_contract_linkage_general_gate_v1.py"

"${PY}" "${PATCHER}"

bash -n scripts/gate_contract_linkage_v1.sh

if ls scripts/gate_*contract*linkage*rc*_v*.sh >/dev/null 2>&1; then
  for f in scripts/gate_*contract*linkage*rc*_v*.sh; do
    bash -n "${f}"
  done
fi

echo "OK"
