#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Fix scripts/recap.py rivalry + export-assemblies blocks (v1) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_fix_recap_py_rivalry_and_export_blocks_v1.py
