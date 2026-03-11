#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: example noop (v1) ==="

PATCHER="scripts/_patch_example_noop_v1.py"

# 0) snapshot (helps show whether anything changed)
before_sha="$(git rev-parse --verify HEAD 2>/dev/null || true)"
before_diff_lines="$(git diff --numstat -- docs/80_indices/ops/CI_Guardrails_Index_v1.0.md 2>/dev/null | awk '{print $1+$2}' || true)"

# 1) compile check
./scripts/py -m py_compile "$PATCHER"

# 2) run patcher
./scripts/py "$PATCHER"

# 3) wrapper sanity
echo "==> bash -n wrapper"
bash -n scripts/patch_example_noop_v1.sh

# 4) lightweight assertions
echo "==> quick assertions"
test -f docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

# 5) report what happened (helpful in logs)
after_diff_stat="$(git diff --stat -- docs/80_indices/ops/CI_Guardrails_Index_v1.0.md 2>/dev/null || true)"
after_diff_lines="$(git diff --numstat -- docs/80_indices/ops/CI_Guardrails_Index_v1.0.md 2>/dev/null | awk '{print $1+$2}' || true)"

if [[ -z "${after_diff_lines}" || "${after_diff_lines}" == "0" ]]; then
  echo "==> result: no-op (already in desired state)"
else
  echo "==> result: changed (diffstat below)"
  echo "$after_diff_stat"
fi

echo "OK"
