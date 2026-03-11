#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Canonical Indices Map + CI index link (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_add_canonical_indices_map_v1.py

echo "==> Verify: new index doc exists"
test -f docs/80_indices/ops/Canonical_Indices_Map_v1.0.md

echo "==> Verify: required links present (grep assertions)"
grep -nF "CI_Guardrails_Index_v1.0.md" docs/80_indices/ops/Canonical_Indices_Map_v1.0.md >/dev/null
grep -nF "Process_Discipline_Index_v1.0.md" docs/80_indices/ops/Canonical_Indices_Map_v1.0.md >/dev/null
grep -nF "Recovery_Workflows_Index_v1.0.md" docs/80_indices/ops/Canonical_Indices_Map_v1.0.md >/dev/null
grep -nF "CI_Patcher_Wrapper_Pairing_Gate_v1.0.md" docs/80_indices/ops/Canonical_Indices_Map_v1.0.md >/dev/null
grep -nF "CI_Cleanliness_Invariant_v1.0.md" docs/80_indices/ops/Canonical_Indices_Map_v1.0.md >/dev/null

echo "==> Verify: CI Guardrails index has discoverability bullet"
grep -nF "Canonical_Indices_Map_v1.0.md" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null

echo "OK"
