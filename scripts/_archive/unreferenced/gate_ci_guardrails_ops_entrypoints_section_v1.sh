#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: CI Guardrails ops entrypoints section (v1) ==="

DOC="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

BEGIN="<!-- SV_BEGIN: ops_entrypoints_hub (v1) -->"
END="<!-- SV_END: ops_entrypoints_hub (v1) -->"

test -f "${DOC}"

# Extract bounded section (fail if missing)
section="$(
  awk -v b="${BEGIN}" -v e="${END}" '
    $0 == b {p=1}
    p {print}
    $0 == e {exit}
  ' "${DOC}"
)"

if [[ -z "${section}" ]]; then
  echo "ERROR: missing bounded ops entrypoints section in ${DOC}"
  exit 1
fi

# Required links must be present inside the bounded section
echo "${section}" | grep -F "Ops_Entrypoints_Hub_v1.0.md" >/dev/null
echo "${section}" | grep -F "Canonical_Indices_Map_v1.0.md" >/dev/null
echo "${section}" | grep -F "Process_Discipline_Index_v1.0.md" >/dev/null
echo "${section}" | grep -F "Recovery_Workflows_Index_v1.0.md" >/dev/null
echo "${section}" | grep -F "Ops_Rules_One_Page_v1.0.md" >/dev/null
echo "${section}" | grep -F "New_Contributor_Orientation_10min_v1.0.md" >/dev/null

echo "OK: ops entrypoints bounded section present + complete."
