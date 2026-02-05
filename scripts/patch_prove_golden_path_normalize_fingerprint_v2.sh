#!/usr/bin/env bash
set -euo pipefail
: "${HISTTIMEFORMAT:=}"
: "${size:=}"

echo "=== Patch wrapper: prove_golden_path normalize fingerprint (v2) ==="

if [ -x "scripts/py" ]; then
  py="scripts/py"
else
  py="${PYTHON:-python}"
fi

$py scripts/_patch_prove_golden_path_normalize_fingerprint_v2.py

echo "==> bash -n: scripts/prove_golden_path.sh"
bash -n scripts/prove_golden_path.sh

echo "==> marker check"
grep -n "SV_PATCH: NAC preflight fingerprint normalization (v2)" scripts/prove_golden_path.sh >/dev/null

echo "OK"
