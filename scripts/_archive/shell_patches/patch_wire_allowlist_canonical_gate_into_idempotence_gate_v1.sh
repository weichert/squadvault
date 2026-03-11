#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire allowlist canonical gate into idempotence gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_wire_allowlist_canonical_gate_into_idempotence_gate_v1.py

echo "==> bash -n (modified gate)"
bash -n scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "==> grep: confirm wiring"
grep -n "gate_patch_idempotence_allowlist_canonical_v1.sh" scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "OK"
