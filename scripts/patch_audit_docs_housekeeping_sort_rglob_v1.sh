#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: audit_docs_housekeeping sort rglob (v1) ==="

python="${PYTHON:-python}"

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

./scripts/py scripts/_patch_audit_docs_housekeeping_sort_rglob_v1.py

echo "==> show diff (no pager)"
GIT_PAGER=cat git diff -- scripts/audit_docs_housekeeping_v1.sh || true

echo "==> rerun filesystem ordering determinism gate"
./scripts/check_filesystem_ordering_determinism.sh

echo "OK"
