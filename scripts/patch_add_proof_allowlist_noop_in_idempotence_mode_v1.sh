#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add proof allowlist noop under SV_IDEMPOTENCE_MODE=1 (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_add_proof_allowlist_noop_in_idempotence_mode_v1.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
${PY} -m py_compile "${PATCHER}"

echo "==> run patcher"
${PY} "${PATCHER}"

echo "==> chmod +x proof"
chmod +x scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh

echo "==> bash -n"
bash -n scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh
bash -n scripts/prove_ci.sh

echo "==> cheap local verification: run proof (requires clean repo)"
if [[ -z "$(git status --porcelain=v1)" ]]; then
  bash scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh
else
  echo "NOTE: skipping local proof run because repo is not clean yet."
fi

echo "OK"
