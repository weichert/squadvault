#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: Rivalry Chronicle export contract relocate required section headings block (v11) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_prove_rivalry_chronicle_export_contract_sections_v11_relocate.py

echo "==> bash syntax check"
bash -n scripts/prove_rivalry_chronicle_end_to_end_v1.sh

echo "==> show window around new_lines + required sections block"
line="$(grep -n 'new_lines = lines\\[:meta_start\\] \\+ meta \\+ lines\\[meta_end\\:\\]' scripts/prove_rivalry_chronicle_end_to_end_v1.sh | head -n1 | cut -d: -f1)"
start=$((line-6))
end=$((line+45))
if [[ "${start}" -lt 1 ]]; then start=1; fi
sed -n "${start},${end}p" scripts/prove_rivalry_chronicle_end_to_end_v1.sh

echo "OK"
