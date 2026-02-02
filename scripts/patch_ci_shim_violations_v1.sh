#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: CI shim violations (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Helper: replace a string literally (macOS + GNU sed compatible)
replace_in_file () {
  local file="$1"
  local from="$2"
  local to="$3"
  if [[ ! -f "$file" ]]; then
    echo "SKIP: missing file: $file"
    return 0
  fi
  if grep -Fq "$from" "$file"; then
    python - <<PY
from pathlib import Path
p = Path("$file")
s = p.read_text()
p.write_text(s.replace("$from", "$to"))
PY
    echo "OK: patched $file"
  else
    echo "OK: no-op $file"
  fi
}

# 1) Replace shim-violating invocations with scripts/py shim
replace_in_file "scripts/prove_eal_calibration_type_a_v1.sh" \
  "PYTHONPATH=src ${PYTHON:-python} -m py_compile" \
  "./scripts/py -m py_compile"

replace_in_file "scripts/prove_tone_engine_type_a_v1.sh" \
  "PYTHONPATH=src ${PYTHON:-python} -m py_compile" \
  "./scripts/py -m py_compile"

replace_in_file "scripts/prove_version_presentation_navigation_type_a_v1.sh" \
  "PYTHONPATH=src ${PYTHON:-python} -m py_compile" \
  "./scripts/py -m py_compile"

replace_in_file "scripts/patch_rc_input_contract_fix_resolve_v4.sh" \
  "PYTHONPATH=src ${PYTHON:-python} -m py_compile" \
  "./scripts/py -m py_compile"

replace_in_file "scripts/patch_rc_input_contract_fix_resolve_v4.sh" \
  "PYTHONPATH=src ${PYTHON:-python} -m unittest -v" \
  "./scripts/py -m unittest -v"

replace_in_file "scripts/patch_rivalry_chronicle_consolidated_v2.sh" \
  "PYTHONPATH=src ${PYTHON:-python} -m py_compile" \
  "./scripts/py -m py_compile"

echo
echo "==> Sanity: shim compliance"
bash scripts/check_shims_compliance.sh
echo "OK"
