#!/usr/bin/env bash
set -euo pipefail

repo_root="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"

cd "${repo_root}"

echo "=== Patch: add CI guardrails surface freeze gate (v1) ==="
PYTHONDONTWRITEBYTECODE=1 ./scripts/py scripts/_patch_add_ci_guardrails_surface_freeze_gate_v1.py

echo "==> Verify bash syntax"
bash -n scripts/gate_ci_guardrails_surface_freeze_v1.sh
bash -n scripts/patch_add_ci_guardrails_surface_freeze_gate_v1.sh

echo "==> Verify prove_ci wiring"
grep -nF 'bash scripts/gate_ci_guardrails_surface_freeze_v1.sh' scripts/prove_ci.sh >/dev/null

echo "==> Verify registry entry"
grep -nF 'scripts/gate_ci_guardrails_surface_freeze_v1.sh' \
  docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv >/dev/null

echo "==> Verify index entry"
grep -nF 'scripts/gate_ci_guardrails_surface_freeze_v1.sh' \
  docs/80_indices/ops/CI_Guardrails_Index_v1.0.md >/dev/null

echo "OK: CI guardrails surface freeze patch applied (v1)"
