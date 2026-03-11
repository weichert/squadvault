#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: RC contract output markers (SV_CONTRACT_NAME/SV_CONTRACT_DOC_PATH) (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_rc_contract_output_contract_name_markers_v1.py

echo "==> bash -n"
bash -n scripts/gate_rivalry_chronicle_output_contract_v1.sh
bash -n scripts/prove_rivalry_chronicle_end_to_end_v1.sh

echo "==> verify exact markers"
NAME="RIVALRY_CHRONICLE_CONTRACT_OUTPUT_V1"
DOC="docs/contracts/rivalry_chronicle_contract_output_v1.md"
grep -Fqx "# SV_CONTRACT_NAME: ${NAME}" scripts/gate_rivalry_chronicle_output_contract_v1.sh
grep -Fqx "# SV_CONTRACT_DOC_PATH: ${DOC}" scripts/gate_rivalry_chronicle_output_contract_v1.sh
grep -Fqx "# SV_CONTRACT_NAME: ${NAME}" scripts/prove_rivalry_chronicle_end_to_end_v1.sh
grep -Fqx "# SV_CONTRACT_DOC_PATH: ${DOC}" scripts/prove_rivalry_chronicle_end_to_end_v1.sh

echo "==> smoke: contract surface completeness proof"
bash scripts/prove_contract_surface_completeness_v1.sh

echo "OK"
