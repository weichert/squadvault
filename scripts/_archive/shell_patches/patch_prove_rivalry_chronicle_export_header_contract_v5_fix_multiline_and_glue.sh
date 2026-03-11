#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: fix Rivalry Chronicle export multiline join + glued out_path.write_text (v5) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_prove_rivalry_chronicle_export_header_contract_v5_fix_multiline_and_glue.py

echo "==> bash syntax check"
bash -n scripts/prove_rivalry_chronicle_end_to_end_v1.sh

echo "==> show window around contract join/write"
line="$(grep -n 'hdr = "# Rivalry Chronicle (v1)"' scripts/prove_rivalry_chronicle_end_to_end_v1.sh | head -n1 | cut -d: -f1)"
start=$((line-5))
end=$((line+45))
if [[ "${start}" -lt 1 ]]; then start=1; fi
sed -n "${start},${end}p" scripts/prove_rivalry_chronicle_end_to_end_v1.sh

echo "OK"
