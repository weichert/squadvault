#!/usr/bin/env bash
set -euo pipefail

# patch_move_python_shim_compliance_exceptions_block_v1
# Idempotent: safe to run twice.

repo_root="$(
  cd "$(dirname "$0")/.." >/dev/null 2>&1
  pwd
)"
cd "${repo_root}"

./scripts/py scripts/_patch_move_python_shim_compliance_exceptions_block_v1.py
