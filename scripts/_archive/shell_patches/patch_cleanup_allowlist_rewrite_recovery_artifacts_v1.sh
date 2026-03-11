#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: cleanup allowlist rewrite recovery artifacts (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} -m py_compile scripts/_patch_cleanup_allowlist_rewrite_recovery_artifacts_v1.py
${PY} scripts/_patch_cleanup_allowlist_rewrite_recovery_artifacts_v1.py

echo "==> smoke: ensure canonical v2 rewrite still compiles"
${PY} -m py_compile scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.py

echo "==> smoke: gate still passes"
bash scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh

echo "OK"
