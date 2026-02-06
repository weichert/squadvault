#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: rewrite stale docs/_import/INBOX references (v1) ==="

python="${PYTHON:-python}"

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

$python scripts/_patch_docs_rewrite_stale_import_refs_v1.py

echo "==> re-run docs housekeeping audit"
./scripts/audit_docs_housekeeping_v1.sh

echo "OK"
