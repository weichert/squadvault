#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix awk reserved word usage in proof registry exactness gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_gate_ci_proof_surface_registry_exactness_awk_var_v1.py

echo "==> bash syntax check"
bash -n scripts/gate_ci_proof_surface_registry_exactness_v1.sh

echo "==> smoke: run gate"
bash scripts/gate_ci_proof_surface_registry_exactness_v1.sh

echo "OK"
