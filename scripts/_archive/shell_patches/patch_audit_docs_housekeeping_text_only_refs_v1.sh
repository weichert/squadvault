#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: audit docs path mentions scan text-only (v1) ==="

python="${PYTHON:-python}"

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

./scripts/py scripts/_patch_audit_docs_housekeeping_text_only_refs_v1.py

echo "==> re-run audit"
./scripts/audit_docs_housekeeping_v1.sh

echo "OK"
