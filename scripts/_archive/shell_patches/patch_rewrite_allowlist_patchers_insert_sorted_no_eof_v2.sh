#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: rewrite allowlist patchers to insert-sorted (NO EOF strings) (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} -m py_compile scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.py
${PY} scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.py

echo "==> py_compile allowlist patchers"
for f in scripts/_patch_allowlist_patch_wrapper_*.py; do
  ${PY} -m py_compile "$f"
done

echo "==> gate"
bash scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh

echo "OK"
