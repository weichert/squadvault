#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Lock E apply wrapper tiny polish (v1) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_lock_e_apply_wrapper_tiny_polish_v1.py"

echo
echo "=== Sanity: py_compile ==="
python -m py_compile "${repo_root}/scripts/patch_apply_lock_e_final_state.sh" >/dev/null 2>&1 || true

echo
echo "OK: tiny polish patch applied."
echo "Tip: to enable sqlite sanity probe, run with:"
echo "  SV_DB_PATH=.local_squadvault.sqlite ./scripts/patch_apply_lock_e_final_state.sh"
