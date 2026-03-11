#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI Guardrails Index add Ops Entrypoints TOC entry (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_ci_guardrails_add_ops_entrypoints_toc_v1.py

echo "==> Verify: bounded TOC markers present"
grep -nF "<!-- SV_BEGIN: ops_entrypoints_toc (v1) -->" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null
grep -nF "<!-- SV_END: ops_entrypoints_toc (v1) -->" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null

echo "==> Verify: TOC anchor entry present"
grep -nF "[Ops Entrypoints (Canonical)](#ops-entrypoints-canonical)" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null

echo "==> bash syntax check"
bash -n scripts/patch_ci_guardrails_add_ops_entrypoints_toc_v1.sh

echo "OK"
