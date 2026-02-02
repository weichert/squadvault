#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: add CI+Docs hardening freeze addendum + docmap link (v1) ==="

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

python="${PYTHON:-python}"
${python} scripts/_patch_docs_add_ci_docs_hardening_freeze_v1.py

echo "==> git diff --name-only"
git diff --name-only || true

echo "OK"
