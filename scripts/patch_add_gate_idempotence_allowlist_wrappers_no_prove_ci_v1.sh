#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add gate_idempotence_allowlist_wrappers_no_prove_ci_v1 (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_add_gate_idempotence_allowlist_wrappers_no_prove_ci_v1.py

chmod +x scripts/gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh

echo "==> bash -n (new gate)"
bash -n scripts/gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh

echo "OK"
