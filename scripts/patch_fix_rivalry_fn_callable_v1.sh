#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Fix rivalry-chronicle fn default to callable (v1) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_fix_rivalry_fn_callable_v1.py
