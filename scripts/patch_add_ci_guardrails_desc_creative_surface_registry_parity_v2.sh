#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PATCHER="scripts/_patch_add_ci_guardrails_desc_creative_surface_registry_parity_v2.py"
TARGET="scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py"

./scripts/py -m py_compile "$PATCHER"
./scripts/py "$PATCHER"

# Sanity: confirm mapping key exists in the DESC dict file
grep -n --fixed-string "scripts/gate_creative_surface_registry_parity_v1.sh" "$TARGET" >/dev/null

bash -n "$0"
echo "OK: patch_add_ci_guardrails_desc_creative_surface_registry_parity_v2"
