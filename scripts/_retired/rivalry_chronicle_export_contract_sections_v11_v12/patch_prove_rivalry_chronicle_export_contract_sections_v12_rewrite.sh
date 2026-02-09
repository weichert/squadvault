#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: Rivalry Chronicle export contract rewrite required section headings block (v12) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_prove_rivalry_chronicle_export_contract_sections_v12_rewrite.py

echo "==> bash syntax check"
bash -n scripts/prove_rivalry_chronicle_end_to_end_v1.sh

echo "==> verify exactly one marker + show around anchor"
grep -n '# --- REQUIRED_SECTION_HEADINGS_V10 ---' scripts/prove_rivalry_chronicle_end_to_end_v1.sh

line="$(grep -n 'new_lines = lines\\[:meta_start\\] \\+ meta \\+ lines\\[meta_end\\:\\]' scripts/prove_rivalry_chronicle_end_to_end_v1.sh | head -n1 | cut -d: -f1)"
start=$((line-6))
end=$((line+55))
if [[ "${start}" -lt 1 ]]; then start=1; fi
sed -n "${start},${end}p" scripts/prove_rivalry_chronicle_end_to_end_v1.sh

echo "OK"
