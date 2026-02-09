#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: retire Rivalry Chronicle section-scaffold patch artifacts (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_retire_rivalry_chronicle_sections_patch_artifacts_v1.py

echo "==> verify removed files are gone"
missing_ok=1
for f in \
  scripts/_patch_prove_rivalry_chronicle_export_contract_sections_v11_relocate.py \
  scripts/patch_prove_rivalry_chronicle_export_contract_sections_v11_relocate.sh \
  scripts/_patch_prove_rivalry_chronicle_export_contract_sections_v12_rewrite.py \
  scripts/patch_prove_rivalry_chronicle_export_contract_sections_v12_rewrite.sh
do
  if [[ -e "$f" ]]; then
    echo "ERROR: still present: $f"
    missing_ok=0
  fi
done

if [[ "$missing_ok" -ne 1 ]]; then
  exit 1
fi

echo "OK"
