#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add CI execution exemptions for local-only proofs (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_registry_add_ci_execution_exempt_locals_v1.py

echo "==> bash syntax check (doc presence only)"
test -f docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md
echo "OK"
