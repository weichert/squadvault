#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: micro-tidy v2 installer (no-op if gate already bash3-safe) (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_micro_tidy_noop_if_gate_safe_in_add_gate_no_prove_ci_v2_v1.py

echo "==> py_compile (v2 patcher)"
${PY} -m py_compile scripts/_patch_add_gate_idempotence_allowlist_wrappers_no_prove_ci_v2.py

echo "==> bash -n (v2 wrapper)"
bash -n scripts/patch_add_gate_idempotence_allowlist_wrappers_no_prove_ci_v2.sh

echo "==> quick prove: running v2 wrapper should not dirty repo"
git status --porcelain=v1 > /tmp/sv_status_before_micro_tidy.txt
bash scripts/patch_add_gate_idempotence_allowlist_wrappers_no_prove_ci_v2.sh >/dev/null
git status --porcelain=v1 > /tmp/sv_status_after_micro_tidy.txt

if ! cmp -s /tmp/sv_status_before_micro_tidy.txt /tmp/sv_status_after_micro_tidy.txt; then
  echo "ERROR: v2 wrapper dirtied repo unexpectedly (micro-tidy invariant violated)" >&2
  echo "==> diff (before vs after)" >&2
  diff -u /tmp/sv_status_before_micro_tidy.txt /tmp/sv_status_after_micro_tidy.txt >&2 || true
  exit 1
fi

echo "OK"
