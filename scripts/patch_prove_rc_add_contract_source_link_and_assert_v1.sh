#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove RC adds contract source-of-truth link + presence assert (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

PATCHER="scripts/_patch_prove_rc_add_contract_source_link_and_assert_v1.py"

echo "==> py_compile patcher"
"${PY}" -m py_compile "${PATCHER}"

echo "==> run patcher"
"${PY}" "${PATCHER}"

echo "==> bash syntax check (prove script)"
bash -n scripts/prove_rivalry_chronicle_end_to_end_v1.sh

echo "==> show insertion windows"
grep -n "Contract source-of-truth: docs/contracts/rivalry_chronicle_output_contract_v1.md" -n -C 2 scripts/prove_rivalry_chronicle_end_to_end_v1.sh || true
grep -n "missing contract source-of-truth" -n -C 2 scripts/prove_rivalry_chronicle_end_to_end_v1.sh || true
