#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add rules_of_engagement discoverability to CI guardrails index (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" -m py_compile scripts/_patch_ci_guardrails_index_add_rules_of_engagement_discoverability_v1.py
"${PY}" scripts/_patch_ci_guardrails_index_add_rules_of_engagement_discoverability_v1.py

echo "==> bash syntax check"
bash -n scripts/patch_ci_guardrails_index_add_rules_of_engagement_discoverability_v1.sh

echo "==> verify needles present"
grep -nF "rules_of_engagement" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
grep -nF "Docs + CI Mutation Policy" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "OK"
