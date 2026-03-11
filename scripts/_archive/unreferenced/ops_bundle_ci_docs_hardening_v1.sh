#!/usr/bin/env bash
set -euo pipefail
echo "=== Ops Bundle: CI + Docs hardening (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/ops_orchestrate.sh \
  ./scripts/patch_ci_cleanliness_finishing_touches_v2.sh \
  ./scripts/patch_audit_docs_housekeeping_text_only_refs_v1.sh \
  ./scripts/patch_audit_docs_housekeeping_sort_rglob_v2.sh
