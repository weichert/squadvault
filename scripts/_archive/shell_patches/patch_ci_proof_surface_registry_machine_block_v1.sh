#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: proof surface registry machine block (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_ci_proof_surface_registry_machine_block_v1.py

echo "==> Sanity: markers present"
DOC="docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"
grep -nF "<!-- SV_PROOF_SURFACE_LIST_v1_BEGIN -->" "${DOC}" >/dev/null
grep -nF "<!-- SV_PROOF_SURFACE_LIST_v1_END -->" "${DOC}" >/dev/null

echo "==> Bash syntax check"
bash -n scripts/gate_ci_proof_surface_registry_exactness_v1.sh

echo "OK"
