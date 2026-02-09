#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: proof-surface gate detect prove invocations only (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_ci_proof_surface_gate_invocation_detection_v1.py

echo "==> py_compile"
"${PY}" -m py_compile scripts/_patch_ci_proof_surface_gate_invocation_detection_v1.py
"${PY}" -m py_compile scripts/_patch_ci_proof_surface_gate_parser_v2.py

echo "==> bash syntax check (gate)"
bash -n scripts/check_ci_proof_surface_matches_registry_v1.sh

echo "==> smoke: run proof-surface gate standalone"
bash scripts/check_ci_proof_surface_matches_registry_v1.sh

echo "OK"
