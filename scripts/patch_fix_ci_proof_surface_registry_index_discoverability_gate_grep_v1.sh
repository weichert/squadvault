#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix discoverability gate grep (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_fix_ci_proof_surface_registry_index_discoverability_gate_grep_v1.py"
GATE="scripts/gate_ci_proof_surface_registry_index_discoverability_v1.sh"
PROVE="scripts/prove_ci.sh"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> bash -n gate + wrapper"
bash -n "${GATE}"
bash -n "scripts/patch_fix_ci_proof_surface_registry_index_discoverability_gate_grep_v1.sh"

echo "==> run gate (must pass)"
bash "${GATE}"

echo "==> prove_ci (expected DIRTY pre-commit)"
bash "${PROVE}" || true

echo "OK"
