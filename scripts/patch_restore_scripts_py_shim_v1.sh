#!/usr/bin/env bash
set -euo pipefail

# patch_restore_scripts_py_shim_v1
# Idempotent wrapper: safe to run twice from clean.

repo_root="$(
  cd "$(dirname "$0")/.." >/dev/null 2>&1
  pwd
)"
cd "${repo_root}"

python3 scripts/_patch_restore_scripts_py_shim_v1.py 2>/dev/null || python scripts/_patch_restore_scripts_py_shim_v1.py
