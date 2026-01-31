#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: rules_of_engagement add docs+CI mutation policy (v1) ==="

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

python="${PYTHON:-python}"
${python} scripts/_patch_rules_of_engagement_add_docs_mutation_policy_v1.py

echo "==> git diff --name-only"
git diff --name-only || true

echo "OK"
