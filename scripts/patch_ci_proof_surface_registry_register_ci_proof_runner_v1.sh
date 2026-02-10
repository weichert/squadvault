#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: register CI proof runner in registry (v1) ==="

if [[ "$#" -ne 2 ]]; then
  echo "FAIL: usage:" >&2
  echo "  $0 \"scripts/prove_xxx_v1.sh\" \"Description...\"" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_ci_proof_surface_registry_register_ci_proof_runner_v1.py "$1" "$2"
