#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: exempt fixture immutability proof from CI execution (v1) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py -m py_compile scripts/_patch_registry_add_ci_execution_exempt_fixture_immutability_proof_v1.py
./scripts/py scripts/_patch_registry_add_ci_execution_exempt_fixture_immutability_proof_v1.py

echo "OK"
