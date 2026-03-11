#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire no-prove-ci recursion guard into idempotence allowlist gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_wire_idempotence_allowlist_no_prove_ci_gate_into_idempotence_gate_v1.py

echo "==> bash -n (modified gate)"
bash -n scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "OK"
