#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs integrity regen postprocess scope -> docs/canonical only (v3) ==="

allowed_paths=(
  "scripts/_patch_docs_integrity_gate_scope_canonical_only_v3.py"
  "scripts/patch_docs_integrity_gate_scope_canonical_only_v3.sh"
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

"$python_bin" scripts/_patch_docs_integrity_gate_scope_canonical_only_v3.py

echo "==> py_compile target patcher"
"$python_bin" -m py_compile scripts/_patch_add_docs_integrity_gate_v1.py

echo "==> smoke: regenerate docs gate (ensures postprocess runs)"
bash scripts/patch_add_docs_integrity_gate_v1.sh >/dev/null

echo "==> docs integrity proof"
bash scripts/prove_docs_integrity_v1.sh

echo "==> full prove"
bash scripts/prove_ci.sh

echo "OK: patch complete (v3). Now commit + push."
