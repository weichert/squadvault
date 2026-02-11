#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: ops index dedupe fixture immutability proof entry (v1) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python -m py_compile scripts/_patch_ops_index_dedupe_fixture_immutability_proof_entry_v1.py
python scripts/_patch_ops_index_dedupe_fixture_immutability_proof_entry_v1.py

echo "OK"
