#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: CI execution exempt creative sharepack determinism proof (v1) ==="

python -m py_compile scripts/_patch_ci_execution_exempt_add_creative_sharepack_determinism_v1.py
./scripts/py scripts/_patch_ci_execution_exempt_add_creative_sharepack_determinism_v1.py

echo "==> sanity: item present in exemption block"
awk '
  /SV_CI_EXECUTION_EXEMPT_v1_BEGIN/ {inblk=1; next}
  /SV_CI_EXECUTION_EXEMPT_v1_END/ {inblk=0; next}
  inblk {print}
' docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md | grep -n "prove_creative_sharepack_determinism_v1.sh"

echo "OK"
