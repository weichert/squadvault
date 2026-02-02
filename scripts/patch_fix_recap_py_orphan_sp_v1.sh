#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Fix scripts/recap.py orphan 'sp =' (Rivalry Chronicle Lock A) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_fix_recap_py_orphan_sp_v1.py
