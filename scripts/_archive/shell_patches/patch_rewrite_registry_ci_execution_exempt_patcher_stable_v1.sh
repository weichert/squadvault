#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: rewrite registry CI execution exempt patcher to be formatting-stable (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> apply rewrite patcher"
"${PY}" -m py_compile scripts/_patch_rewrite_registry_ci_execution_exempt_patcher_stable_v1.py
"${PY}" scripts/_patch_rewrite_registry_ci_execution_exempt_patcher_stable_v1.py

echo "==> verify rewritten patcher compiles"
"${PY}" -m py_compile scripts/_patch_registry_add_ci_execution_exempt_locals_v1.py

echo "OK"
