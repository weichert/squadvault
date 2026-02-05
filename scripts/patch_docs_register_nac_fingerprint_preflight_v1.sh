#!/usr/bin/env bash
set -euo pipefail
: "${HISTTIMEFORMAT:=}"

echo "=== Patch wrapper: docs register NAC fingerprint preflight (v1) ==="

if [ -x "scripts/py" ]; then
  py="scripts/py"
else
  py="${PYTHON:-python}"
fi

$py scripts/_patch_docs_register_nac_fingerprint_preflight_v1.py

echo "==> verify: marker present"
grep -n "SV_PATCH: nac fingerprint preflight doc (v1)" docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md
grep -n "SV_PATCH: nac fingerprint preflight doc (v1)" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "==> prove docs integrity"
bash scripts/prove_docs_integrity_v1.sh

echo "OK"
