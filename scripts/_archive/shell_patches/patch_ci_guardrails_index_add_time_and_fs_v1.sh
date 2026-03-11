#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: CI Guardrails Index add filesystem + time determinism (v1) ==="

python="${PYTHON:-python}"

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

./scripts/py scripts/_patch_ci_guardrails_index_add_time_and_fs_v1.py

echo "==> show diff"
git diff -- docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true

echo "OK"
