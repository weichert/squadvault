#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add missing local proofs to CI proof surface registry (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_ci_proof_surface_registry_add_missing_local_proofs_v1.py

echo "==> verify markers + entries"
REGISTRY_DOC="docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"
grep -n 'PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1_' "${REGISTRY_DOC}"
grep -n 'prove_local_clean_then_ci_v3.sh' "${REGISTRY_DOC}"
grep -n 'prove_local_shell_hygiene_v1.sh' "${REGISTRY_DOC}"

echo "OK"
