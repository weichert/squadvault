#!/usr/bin/env bash
set -euo pipefail
: "${HISTTIMEFORMAT:=}"

echo "=== Patch wrapper: dedupe prove_ci golden path comment (v1) ==="

if [ -x "scripts/py" ]; then
  py="scripts/py"
else
  py="${PYTHON:-python}"
fi

$py scripts/_patch_dedupe_prove_ci_golden_path_comment_v1.py

echo "==> bash -n: prove_ci.sh"
bash -n scripts/prove_ci.sh

echo "==> golden path block (sanity):"
grep -n "prove_golden_path\.sh" scripts/prove_ci.sh

echo "OK"
