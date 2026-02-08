#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: repair broken allowlist patchers (split f-strings w/ quoted {w}) (v5) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} -m py_compile scripts/_patch_repair_broken_allowlist_patchers_newline_in_quote_v5.py
${PY} scripts/_patch_repair_broken_allowlist_patchers_newline_in_quote_v5.py

echo "==> py_compile offenders"
for f in \
  scripts/_patch_allowlist_patch_wrapper_add_gate_ops_indices_no_autofill_placeholders_v1.py \
  scripts/_patch_allowlist_patch_wrapper_bulk_index_ci_guardrails_entrypoints_v1.py \
  scripts/_patch_allowlist_patch_wrapper_cleanup_ci_guardrails_ops_entrypoint_parity_iterations_v1.py \
  scripts/_patch_allowlist_patch_wrapper_docs_fill_ci_guardrails_autofill_descriptions_v1.py \
  scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v4.py \
  scripts/_patch_allowlist_patch_wrapper_sync_add_gate_patcher_ci_guardrails_ops_entrypoint_parity_v3.py
do
  ${PY} -m py_compile "${f}"
done

echo "OK"
