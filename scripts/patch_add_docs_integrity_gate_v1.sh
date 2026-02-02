#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add docs integrity gate (v1) ==="

# Cleanliness precheck (hard)
# Allow ONLY the known milestone surface (staged or not) to exist at start.
allowed_paths=(
  "scripts/_patch_add_docs_integrity_gate_v1.py"
  "scripts/patch_add_docs_integrity_gate_v1.sh"
  "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
  "docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"
  "scripts/prove_ci.sh"
  "docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md"
  "scripts/check_docs_integrity_v1.py"
  "scripts/prove_docs_integrity_v1.sh"
)

dirty="$(git status --porcelain=v1)"
if [ -n "$dirty" ]; then
  remain="$dirty"
  for p in "${allowed_paths[@]}"; do
    remain="$(printf "%s\n" "$remain" | grep -v " ${p}\$" || true)"
  done
  if [ -n "$remain" ]; then
    echo "FAIL: repo not clean before patch (unexpected changes present)."
    printf "%s\n" "$remain"
    exit 1
  fi
fi

python_bin="${PYTHON:-python}"

"$python_bin" scripts/_patch_add_docs_integrity_gate_v1.py

echo "==> bash -n new proof runner"
bash -n scripts/prove_docs_integrity_v1.sh

echo "==> py_compile patcher + checker"
"$python_bin" -m py_compile scripts/_patch_add_docs_integrity_gate_v1.py
"$python_bin" -m py_compile scripts/check_docs_integrity_v1.py

echo "==> gate self-test (positive)"
bash scripts/prove_docs_integrity_v1.sh

echo "==> full prove suite"
bash scripts/prove_ci.sh

echo "==> cleanliness postcheck (hard)"
if [ -n "$(git status --porcelain=v1)" ]; then
  echo "FAIL: repo not clean after patch."
  git status --porcelain=v1
  exit 1
fi

echo "OK: patch_add_docs_integrity_gate_v1 complete"
