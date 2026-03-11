#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs clarify example_noop vs TEMPLATE usage (v1) ==="

PY="./scripts/py"
if [[ ! -x "$PY" ]]; then
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_docs_clarify_example_vs_template_v1.py

echo "==> verify pattern doc updated"
grep -q 'EXAMPLE_VS_TEMPLATE_CLARITY_v1_BEGIN' docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md
grep -q 'scripts/_patch_example_noop_v1.py' docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md
grep -q 'scripts/_patch_TEMPLATE_v0.py' docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md

echo "==> verify gate doc updated"
grep -q 'EXAMPLE_VS_TEMPLATE_CLARITY_v1_BEGIN' docs/80_indices/ops/CI_Patcher_Wrapper_Pairing_Gate_v1.0.md
grep -q 'docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md' docs/80_indices/ops/CI_Patcher_Wrapper_Pairing_Gate_v1.0.md
grep -q 'scripts/patch_example_noop_v1.sh' docs/80_indices/ops/CI_Patcher_Wrapper_Pairing_Gate_v1.0.md

echo "OK"
