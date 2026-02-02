#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: audit_docs_housekeeping sort rglob (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

target="scripts/audit_docs_housekeeping_v1.sh"

# If already sorted, this patch is a no-op by definition.
if grep -q 'for p in sorted(root\.rglob(' "${target}"; then
  echo "OK: rglob loop already sorted (v2 no-op)."
  exit 0
fi

# Otherwise defer to the original v1 patch wrapper (keeps v1 intact).
echo "NOTE: rglob loop not yet sorted; delegating to v1 patch wrapper."
./scripts/patch_audit_docs_housekeeping_sort_rglob_v1.sh
