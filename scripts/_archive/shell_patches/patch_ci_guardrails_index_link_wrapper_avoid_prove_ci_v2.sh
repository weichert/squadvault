#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI guardrails index link wrapper avoids prove_ci cleanliness trap (v2) ==="

allowed_paths=(
  "scripts/_patch_ci_guardrails_index_link_wrapper_avoid_prove_ci_v2.py"
  "scripts/patch_ci_guardrails_index_link_wrapper_avoid_prove_ci_v2.sh"
)

dirty="$(git status --porcelain=v1)"
if [ -n "$dirty" ]; then
  remain="$dirty"
  for ap in "${allowed_paths[@]}"; do
    remain="$(printf "%s\n" "$remain" | grep -v " ${ap}$" || true)"
  done
  if [ -n "$remain" ]; then
    echo "FAIL: repo not clean before patch (unexpected changes present)."
    printf "%s\n" "$remain"
    exit 1
  fi
fi

python_bin="${PYTHON:-python}"

./scripts/py scripts/_patch_ci_guardrails_index_link_wrapper_avoid_prove_ci_v2.py

echo "==> bash -n target"
bash -n scripts/patch_ci_guardrails_index_add_docs_integrity_link_v1.sh

echo "==> smoke: run wrapper (should NOT run prove_ci anymore)"
bash scripts/patch_ci_guardrails_index_add_docs_integrity_link_v1.sh >/dev/null

echo "OK: patch applied (v2). Now git add + commit + push."
