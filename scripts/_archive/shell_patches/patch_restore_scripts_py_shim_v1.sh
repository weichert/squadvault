#!/usr/bin/env bash
set -euo pipefail

# patch_restore_scripts_py_shim_v1
# Idempotent wrapper: safe to run twice from clean.
#
# NOTE (bootstrap exception):
# This wrapper may need to run when scripts/py is missing or empty.
# In that case, it bootstraps via python3/python exactly once to restore scripts/py,
# then subsequent runs use ./scripts/py normally.

repo_root="$(
  cd "$(dirname "$0")/.." >/dev/null 2>&1
  pwd
)"
cd "${repo_root}"

# If scripts/py exists and is non-empty, use it (canonical path).
if [[ -s "./scripts/py" ]]; then
  ./scripts/py scripts/_patch_restore_scripts_py_shim_v1.py
  exit 0
fi

# Bootstrap only when scripts/py is missing/empty.
if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/_patch_restore_scripts_py_shim_v1.py
fi
if command -v python >/dev/null 2>&1; then
  exec python scripts/_patch_restore_scripts_py_shim_v1.py
fi

echo "ERROR: cannot bootstrap scripts/py — python3/python not found" >&2
exit 127
