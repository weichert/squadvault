#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add New Contributor Orientation (10 min) + map link (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_add_new_contributor_orientation_10min_v1.py

echo "==> Verify: new doc exists"
test -f docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md

echo "==> Verify: required links present (grep assertions)"
grep -nF "../../canon_pointers/How_to_Read_SquadVault_v1.0.md" docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md >/dev/null
grep -nF "../../process/rules_of_engagement.md" docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md >/dev/null
grep -nF "../../process/Canonical_Patcher_Wrapper_Pattern_v1.0.md" docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md >/dev/null
grep -nF "Canonical_Indices_Map_v1.0.md" docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md >/dev/null
grep -nF "Ops_Rules_One_Page_v1.0.md" docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md >/dev/null
grep -nF "Recovery_Workflows_Index_v1.0.md" docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md >/dev/null
grep -nF "CI_Guardrails_Index_v1.0.md" docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md >/dev/null

echo "==> Verify: day-1 commands present"
grep -nF "bash scripts/prove_ci.sh" docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md >/dev/null
grep -nF "bash scripts/patch_example_noop_v1.sh" docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md >/dev/null
grep -nF "git status --porcelain=v1" docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md >/dev/null

echo "==> Verify: Canonical Indices Map has discoverability bullet"
grep -nF "New_Contributor_Orientation_10min_v1.0.md" docs/80_indices/ops/Canonical_Indices_Map_v1.0.md >/dev/null

echo "OK"
