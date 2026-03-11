#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PATCHER="scripts/_patch_creative_surface_registry_doc_v1.py"
DOC="docs/80_indices/ops/Creative_Surface_Registry_v1.0.md"
INDEX="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

./scripts/py -m py_compile "$PATCHER"
./scripts/py "$PATCHER"

# Sanity: registry doc exists + markers present
test -f "$DOC"
grep -n --fixed-string "SV_CREATIVE_SURFACE_REGISTRY_V1_BEGIN" "$DOC" >/dev/null
grep -n --fixed-string "SV_CREATIVE_SURFACE_REGISTRY_V1_END" "$DOC" >/dev/null

# Sanity: ops index bounded section now references the doc
grep -n --fixed-string "Creative_Surface_Registry_v1.0.md" "$INDEX" >/dev/null

bash -n "$0"
echo "OK: patch_creative_surface_registry_doc_v1"
