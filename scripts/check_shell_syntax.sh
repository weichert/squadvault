#!/usr/bin/env bash
set -euo pipefail

echo "=== Check: bash -n on scripts/*.sh ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

fail=0
for f in scripts/*.sh; do
  [[ -f "$f" ]] || continue
  if ! bash -n "$f"; then
    echo "FAIL: bash -n $f" >&2
    fail=1
  fi
done

if [[ "$fail" -ne 0 ]]; then
  echo "ERROR: shell syntax check failed" >&2
  exit 2
fi

echo "OK: all scripts/*.sh pass bash -n"
