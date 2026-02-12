#!/usr/bin/env bash
set -euo pipefail

# Gate: CI runtime envelope (v1)
# - Enforces a soft time budget for prove_ci (measured externally by prove_ci)
# - Enforces proof count invariants when provided
#
# Inputs (optional env):
#   SV_CI_RUNTIME_BUDGET_SECONDS  (default 180)
#   SV_CI_RUNTIME_SECONDS         (required for runtime check)
#   SV_CI_PROOF_COUNT_EXPECTED    (optional; if set, must match SV_CI_PROOF_COUNT_ACTUAL)
#   SV_CI_PROOF_COUNT_ACTUAL      (optional; required if EXPECTED is set)

budget="${SV_CI_RUNTIME_BUDGET_SECONDS:-180}"

if [ -z "${SV_CI_RUNTIME_SECONDS:-}" ]; then
  echo "SKIP: SV_CI_RUNTIME_SECONDS not provided (runtime check not evaluated)."
else
  rt="${SV_CI_RUNTIME_SECONDS}"
  if [ "${rt}" -gt "${budget}" ]; then
    echo "ERROR: CI runtime exceeded budget."
    echo "  runtime_seconds=${rt}"
    echo "  budget_seconds=${budget}"
    exit 1
  fi
  echo "OK: runtime within budget (${rt}s <= ${budget}s)"
fi

if [ -n "${SV_CI_PROOF_COUNT_EXPECTED:-}" ]; then
  if [ -z "${SV_CI_PROOF_COUNT_ACTUAL:-}" ]; then
    echo "ERROR: SV_CI_PROOF_COUNT_EXPECTED is set but SV_CI_PROOF_COUNT_ACTUAL is missing."
    exit 1
  fi
  if [ "${SV_CI_PROOF_COUNT_ACTUAL}" != "${SV_CI_PROOF_COUNT_EXPECTED}" ]; then
    echo "ERROR: proof count drift detected."
    echo "  expected=${SV_CI_PROOF_COUNT_EXPECTED}"
    echo "  actual=${SV_CI_PROOF_COUNT_ACTUAL}"
    exit 1
  fi
  echo "OK: proof count matches expected (${SV_CI_PROOF_COUNT_ACTUAL})"
fi

exit 0
