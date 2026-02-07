#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire index discoverability gate into prove_ci (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_wire_ci_proof_surface_registry_index_discoverability_gate_v3.py"
PROVE="scripts/prove_ci.sh"
GATE="scripts/gate_ci_proof_surface_registry_index_discoverability_v1.sh"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> bash -n gate + prove_ci + wrapper"
bash -n "${GATE}"
bash -n "${PROVE}"
bash -n "scripts/patch_wire_ci_proof_surface_registry_index_discoverability_gate_v3.sh"

echo "==> grep: prove_ci wired to gate"
grep -nF 'gate_ci_proof_surface_registry_index_discoverability_v1.sh' "${PROVE}"
grep -nF 'prove_ci_wire_ci_proof_surface_registry_index_discoverability_gate_v3' "${PROVE}"

echo "==> run gate (should pass on current index)"
bash "${GATE}"

echo "==> prove_ci (expected DIRTY pre-commit)"
bash scripts/prove_ci.sh || true

echo "OK"
