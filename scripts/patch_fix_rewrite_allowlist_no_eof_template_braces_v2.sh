#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix NO-EOF rewrite TEMPLATE brace escaping (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_fix_rewrite_allowlist_no_eof_template_braces_v2.py
${PY} -m py_compile scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.py

echo "OK"
