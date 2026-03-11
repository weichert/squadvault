#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove SV_CONTRACT_NAME markers from non-enforcement RC scripts (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_rc_remove_non_enforcement_contract_name_markers_v1.py

echo "==> Spot-check: ensure no SV_CONTRACT_NAME remains in non-enforcement scripts"
grep -n "^[[:space:]]*# SV_CONTRACT_NAME:" scripts/generate_rivalry_chronicle_v1.sh scripts/persist_rivalry_chronicle_v1.sh scripts/rivalry_chronicle_generate_v1.sh && {
  echo "ERROR: SV_CONTRACT_NAME still present (unexpected)"
  exit 1
} || true

echo "==> bash -n"
bash -n scripts/generate_rivalry_chronicle_v1.sh
bash -n scripts/persist_rivalry_chronicle_v1.sh
bash -n scripts/rivalry_chronicle_generate_v1.sh

echo "OK"
