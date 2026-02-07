#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: no double scripts prefix (v1) ==="

# Primary target: prove_ci (most likely place to regress)
TARGETS=(
  "scripts/prove_ci.sh"
)

for t in "${TARGETS[@]}"; do
  test -f "${t}"
  if grep -nF "scripts/scripts/" "${t}" >/dev/null; then
    echo "ERROR: detected forbidden 'scripts/scripts/' in ${t}"
    grep -nF "scripts/scripts/" "${t}" || true
    exit 1
  fi
done

echo "OK: no 'scripts/scripts/' found in gate targets."
