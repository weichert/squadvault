#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs integrity gate header scope -> docs/canonical only (v1) ==="

allowed_paths=(
  "scripts/_patch_docs_integrity_gate_scope_canonical_only_v1.py"
  "scripts/patch_docs_integrity_gate_scope_canonical_only_v1.sh"
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

./scripts/py scripts/_patch_docs_integrity_gate_scope_canonical_only_v1.py

echo "==> py_compile patcher + checker"
"$python_bin" -m py_compile \
  scripts/_patch_docs_integrity_gate_scope_canonical_only_v1.py \
  scripts/check_docs_integrity_v1.py \
  scripts/_patch_add_docs_integrity_gate_v1.py

echo "==> smoke: docs integrity proof (expected to pass header check for docs/canonical only)"
bash scripts/prove_docs_integrity_v1.sh

echo "==> full prove"
bash scripts/prove_ci.sh

echo "OK: patch complete"
