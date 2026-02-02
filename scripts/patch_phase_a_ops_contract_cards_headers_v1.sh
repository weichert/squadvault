#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: Phase A ops contract cards — prepend canonical header (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python}"
$python scripts/_patch_phase_a_ops_contract_cards_headers_v1.py

echo
echo "OK"
