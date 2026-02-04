#!/usr/bin/env bash
set -euo pipefail
: "${HISTTIMEFORMAT:=}"

echo "=== Patch wrapper: restore prove_ci tail with rivalry (v1) ==="

if [ -x "scripts/py" ]; then
  py="scripts/py"
else
  py="${PYTHON:-python}"
fi

$py scripts/_patch_restore_prove_ci_tail_with_rivalry_v1.py

echo "==> bash -n: prove_ci.sh"
bash -n scripts/prove_ci.sh

echo "==> sanity: rivalry invocation present"
grep -n "prove_rivalry_chronicle_end_to_end_v1\.sh" scripts/prove_ci.sh

echo "OK"
