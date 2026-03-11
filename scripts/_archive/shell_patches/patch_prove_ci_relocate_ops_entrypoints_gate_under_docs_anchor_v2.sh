#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci relocate ops entrypoints gate under docs_gates anchor (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_ci_relocate_ops_entrypoints_gate_under_docs_anchor_v2.py

echo "==> Verify: prove_ci references the v2 gate"
grep -nF "gate_ci_guardrails_ops_entrypoints_section_v2.sh" scripts/prove_ci.sh >/dev/null

echo "==> Verify: gate block is directly under docs_gates anchor and echo-safe"
awk '
  $0=="# === SV_ANCHOR: docs_gates (v1) ==="{p=1}
  p && $0=="# === /SV_ANCHOR: docs_gates (v1) ==="{getline; print; getline; print; getline; print; exit}
' scripts/prove_ci.sh | grep -F 'echo "==> Gate: CI Guardrails ops entrypoints section + TOC (v2)"' >/dev/null

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/patch_prove_ci_relocate_ops_entrypoints_gate_under_docs_anchor_v2.sh

echo "OK"
