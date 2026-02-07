#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: idempotence gate sets SV_IDEMPOTENCE_MODE (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_gate_patch_wrapper_idempotence_set_env_v1.py"
GATE="scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> bash -n gate + wrapper"
bash -n "${GATE}"
bash -n "scripts/patch_gate_patch_wrapper_idempotence_set_env_v1.sh"

echo "==> grep: gate runs wrappers with SV_IDEMPOTENCE_MODE"
grep -nF 'SV_IDEMPOTENCE_MODE=1 bash' "${GATE}"

echo "OK"
