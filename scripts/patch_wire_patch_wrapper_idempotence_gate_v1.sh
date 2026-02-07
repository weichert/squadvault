#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire patch-wrapper idempotence gate into prove_ci (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_wire_patch_wrapper_idempotence_gate_v1.py"
PROVE="scripts/prove_ci.sh"
GATE="scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh"
ALLOWLIST="scripts/patch_idempotence_allowlist_v1.txt"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> bash -n (gate + prove_ci + wrapper)"
bash -n "${GATE}"
bash -n "${PROVE}"
bash -n "scripts/patch_wire_patch_wrapper_idempotence_gate_v1.sh"

echo "==> grep: prove_ci references gate"
grep -nF 'gate_patch_wrapper_idempotence_allowlist_v1.sh' "${PROVE}"
grep -nF 'prove_ci_wire_patch_wrapper_idempotence_gate_v1' "${PROVE}"
grep -nF 'patch_idempotence_allowlist_v1.txt' "${GATE}" "${ALLOWLIST}" >/dev/null || true

echo "==> prove_ci (expected DIRTY pre-commit)"
bash scripts/prove_ci.sh || true

echo "OK"
