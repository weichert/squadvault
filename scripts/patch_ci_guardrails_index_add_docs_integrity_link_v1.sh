#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI guardrails index add docs integrity invariant link (v1) ==="

allowed_paths=(
  "scripts/_patch_ci_guardrails_index_add_docs_integrity_link_v1.py"
  "scripts/patch_ci_guardrails_index_add_docs_integrity_link_v1.sh"
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

echo "==> run patcher"
"$python_bin" scripts/_patch_ci_guardrails_index_add_docs_integrity_link_v1.py

echo "==> bash -n sanity"
bash -n scripts/patch_ci_guardrails_index_add_docs_integrity_link_v1.sh

echo "==> docs integrity proof"
bash scripts/prove_docs_integrity_v1.sh

echo "==> full prove"
bash scripts/prove_ci.sh

echo "OK: patch complete (v1). Now git add + commit + push."
