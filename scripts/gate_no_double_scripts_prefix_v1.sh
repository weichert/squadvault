#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: no double scripts prefix (v1) ==="

# Primary target: prove_ci (most likely place to regress)
TARGETS=(
  "scripts/prove_ci.sh"
)

for t in "${TARGETS[@]}"; do
  test -f "${t}"
  if DOUBLE="scripts/""scripts/"; grep -nF "${DOUBLE}" "${t}" >/dev/null; then
    echo "ERROR: detected forbidden double scripts prefix in ${t}"
    DOUBLE="scripts/""scripts/"; grep -nF "${DOUBLE}" "${t}" || true
    exit 1
  fi
done

echo "OK: no 'scripts/scripts/' found in gate targets."
