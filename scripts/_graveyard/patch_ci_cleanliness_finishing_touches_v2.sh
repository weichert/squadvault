#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: CI cleanliness finishing touches (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

target="scripts/prove_ci.sh"

# Sentinel(s): if these are present, the finishing touches are already applied.
# (Derived from the CI output you showed.)
if grep -q 'OK: CI working tree remained clean (guardrail enforced)\.' "${target}" \
  || grep -q 'OK: CI working tree remained clean (guardrail enforced)' "${target}"; then
  echo "OK: prove_ci already contains cleanliness success marker (v2 no-op)."
  exit 0
fi

echo "NOTE: finishing touches not detected; delegating to v1 patch wrapper."
./scripts/patch_ci_cleanliness_finishing_touches_v1.sh
