#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix wire-gate patcher syntax + wire gate into prove_ci (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> fix patcher syntax"
${PY} -m py_compile scripts/_patch_fix_wire_gate_no_obsolete_allowlist_rewrite_artifacts_syntax_v1.py
${PY} scripts/_patch_fix_wire_gate_no_obsolete_allowlist_rewrite_artifacts_syntax_v1.py

echo "==> compile wire patcher"
${PY} -m py_compile scripts/_patch_prove_ci_wire_gate_no_obsolete_allowlist_rewrite_artifacts_v1.py

echo "==> run wire wrapper (should now work)"
bash scripts/patch_prove_ci_wire_gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh

echo "==> idempotence smoke (run again)"
bash scripts/patch_prove_ci_wire_gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh

echo "==> prove_ci contains gate line"
grep -n "gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh" scripts/prove_ci.sh

echo "OK"
