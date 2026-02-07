#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: index CI proof surface registry gate discoverability (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_index_ci_proof_surface_registry_discoverability_v1.py"
INDEX="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> bash -n wrapper"
bash -n "scripts/patch_index_ci_proof_surface_registry_discoverability_v1.sh"

echo "==> grep: marker + gate path present in index"
grep -nF "<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->" "${INDEX}"
grep -nF "scripts/gate_ci_proof_surface_registry_v1.sh" "${INDEX}"

echo "==> prove_ci (expected DIRTY pre-commit)"
bash scripts/prove_ci.sh || true

echo "OK"
