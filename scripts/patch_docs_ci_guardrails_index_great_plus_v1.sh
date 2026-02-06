#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: CI Guardrails Index Great+ tidy (v1) ==="

./scripts/py -m py_compile scripts/_patch_docs_ci_guardrails_index_great_plus_v1.py
./scripts/py scripts/_patch_docs_ci_guardrails_index_great_plus_v1.py

echo "==> bash -n wrapper"
bash -n scripts/patch_docs_ci_guardrails_index_great_plus_v1.sh

echo "==> preview top (sanity)"
sed -n '1,70p' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "==> verify NAC block now lives under Active Guardrails"
awk '
  /^## Active Guardrails$/ {in=1}
  in && /SV_PATCH: nac fingerprint preflight doc/ {found=1}
  END { if(found) print "OK: NAC block under Active Guardrails"; else { print "ERROR: NAC block not under Active Guardrails"; exit 1 } }
' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "==> verify local-only boundary line"
grep -n "_CI never invokes anything in this section._" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null
echo "OK: local-only boundary line present"

echo "OK"
