#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: register-ci-proof-runner patcher no-op write (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_ci_proof_surface_registry_register_ci_proof_runner_noop_write_v1.py
