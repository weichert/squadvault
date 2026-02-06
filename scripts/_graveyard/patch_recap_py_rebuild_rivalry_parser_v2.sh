#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/recap.py — rebuild rivalry-chronicle parser (indent-safe) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_recap_py_rebuild_rivalry_parser_v2.py
