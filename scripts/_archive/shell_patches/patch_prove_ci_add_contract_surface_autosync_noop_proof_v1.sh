#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci adds contract surface autosync no-op proof (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_ci_add_contract_surface_autosync_noop_proof_v1.py
