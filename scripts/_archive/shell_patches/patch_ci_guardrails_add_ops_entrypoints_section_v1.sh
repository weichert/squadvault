#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI Guardrails Index canonical ops entrypoints section (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_ci_guardrails_add_ops_entrypoints_section_v1.py

echo "==> Verify: bounded section markers present"
grep -nF "<!-- SV_BEGIN: ops_entrypoints_hub (v1) -->" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null
grep -nF "<!-- SV_END: ops_entrypoints_hub (v1) -->" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null

echo "==> Verify: required links present"
grep -nF "Ops_Entrypoints_Hub_v1.0.md" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null
grep -nF "Canonical_Indices_Map_v1.0.md" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null
grep -nF "Process_Discipline_Index_v1.0.md" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null
grep -nF "Recovery_Workflows_Index_v1.0.md" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null
grep -nF "Ops_Rules_One_Page_v1.0.md" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null
grep -nF "New_Contributor_Orientation_10min_v1.0.md" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null

echo "==> bash syntax check"
bash -n scripts/patch_ci_guardrails_add_ops_entrypoints_section_v1.sh

echo "OK"
