#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Ops Entrypoints Hub + map link (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_add_ops_entrypoints_hub_v1.py

echo "==> Verify: new doc exists"
test -f docs/80_indices/ops/Ops_Entrypoints_Hub_v1.0.md

echo "==> Verify: required links present (grep assertions)"
grep -nF "CI_Guardrails_Index_v1.0.md" docs/80_indices/ops/Ops_Entrypoints_Hub_v1.0.md >/dev/null
grep -nF "Canonical_Indices_Map_v1.0.md" docs/80_indices/ops/Ops_Entrypoints_Hub_v1.0.md >/dev/null
grep -nF "Process_Discipline_Index_v1.0.md" docs/80_indices/ops/Ops_Entrypoints_Hub_v1.0.md >/dev/null
grep -nF "Recovery_Workflows_Index_v1.0.md" docs/80_indices/ops/Ops_Entrypoints_Hub_v1.0.md >/dev/null
grep -nF "Ops_Rules_One_Page_v1.0.md" docs/80_indices/ops/Ops_Entrypoints_Hub_v1.0.md >/dev/null
grep -nF "New_Contributor_Orientation_10min_v1.0.md" docs/80_indices/ops/Ops_Entrypoints_Hub_v1.0.md >/dev/null

echo "==> Verify: Canonical Indices Map has discoverability bullet"
grep -nF "Ops_Entrypoints_Hub_v1.0.md" docs/80_indices/ops/Canonical_Indices_Map_v1.0.md >/dev/null

echo "OK"
