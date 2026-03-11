#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix gate_idempotence_allowlist_wrappers_no_prove_ci_v1 (no mapfile) (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_fix_gate_idempotence_allowlist_wrappers_no_prove_ci_no_mapfile_v1.py

echo "==> bash -n (gate)"
bash -n scripts/gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh

echo "==> run gate"
bash scripts/gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh

echo "OK"
