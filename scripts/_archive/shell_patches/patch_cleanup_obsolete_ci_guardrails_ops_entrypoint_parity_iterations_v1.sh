#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: cleanup obsolete CI guardrails ops entrypoint parity iterations (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_cleanup_obsolete_ci_guardrails_ops_entrypoint_parity_iterations_v1.py

echo "==> verify removed files are gone (best-effort)"
for f in \
  scripts/_patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v1.py \
  scripts/patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v1.sh \
  scripts/_patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v2.py \
  scripts/patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v2.sh \
  scripts/_patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v3.py \
  scripts/patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v3.sh \
  scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v1.py \
  scripts/patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v1.sh \
  scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v2.py \
  scripts/patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v2.sh \
  scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v3.py \
  scripts/patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v3.sh
do
  if [[ -e "$f" ]]; then
    echo "ERROR: still exists: $f" >&2
    exit 1
  fi
done

echo "OK"
