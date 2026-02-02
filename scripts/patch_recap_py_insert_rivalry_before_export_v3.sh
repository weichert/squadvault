#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/recap.py — insert rivalry-chronicle before export-assemblies (v3) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_recap_py_insert_rivalry_before_export_v3.py
