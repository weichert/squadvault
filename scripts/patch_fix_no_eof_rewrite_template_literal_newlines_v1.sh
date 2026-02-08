#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix NO-EOF rewrite TEMPLATE literal newline-in-quotes (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} -m py_compile scripts/_patch_fix_no_eof_rewrite_template_literal_newlines_v1.py
${PY} scripts/_patch_fix_no_eof_rewrite_template_literal_newlines_v1.py
${PY} -m py_compile scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.py

echo "OK"
