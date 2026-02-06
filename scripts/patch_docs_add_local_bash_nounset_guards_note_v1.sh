#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: docs add local bash nounset guards note (v1) ==="

./scripts/py scripts/_patch_docs_add_local_bash_nounset_guards_note_v1.py

echo "==> bash -n wrapper"
bash -n scripts/patch_docs_add_local_bash_nounset_guards_note_v1.sh

echo "==> confirm doc header"
sed -n '1,25p' docs/80_indices/ops/Local_Bash_Nounset_Guards_v1.0.md

echo "==> confirm index link"
grep -n "Local Bash Nounset Guards" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true

echo "OK"
