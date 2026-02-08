#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: Ops indices must not contain autofill placeholders (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

needle="— (autofill) describe gate purpose"
root="docs/80_indices/ops"

if grep -nR -- "${needle}" "${root}" >/dev/null; then
  echo "ERROR: found autofill placeholders in ${root}:"
  grep -nR -- "${needle}" "${root}" || true
  exit 1
fi

echo "OK: no autofill placeholders found in ${root}"
