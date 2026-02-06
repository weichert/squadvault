#!/usr/bin/env bash
set -euo pipefail
: "${HISTTIMEFORMAT:=}"

echo "=== Patch wrapper: rewrite prove_ci golden path block strict (v1) ==="

if [ -x "scripts/py" ]; then
  py="scripts/py"
else
  py="${PYTHON:-python}"
fi

./scripts/py scripts/_patch_rewrite_prove_ci_golden_path_block_strict_v1.py

echo "==> bash -n: prove_ci.sh"
bash -n scripts/prove_ci.sh

echo "==> golden path block (sanity):"
grep -n "prove_golden_path\.sh" scripts/prove_ci.sh
echo "==> strict markers:"
grep -n "SV_STRICT_EXPORTS=1" scripts/prove_ci.sh

echo "OK"
