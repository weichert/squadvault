#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: add local shell hygiene helper + index entry (v1) ==="

./scripts/py -m py_compile scripts/_patch_docs_add_local_shell_hygiene_helper_v1.py
./scripts/py scripts/_patch_docs_add_local_shell_hygiene_helper_v1.py

echo "==> bash -n wrapper"
bash -n scripts/patch_docs_add_local_shell_hygiene_helper_v1.sh

echo "==> bash -n helper"
bash -n scripts/prove_local_shell_hygiene_v1.sh

echo "==> confirm index mentions helper"
grep -n "prove_local_shell_hygiene_v1.sh" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true

echo "==> run helper"
bash scripts/prove_local_shell_hygiene_v1.sh

echo "OK"
