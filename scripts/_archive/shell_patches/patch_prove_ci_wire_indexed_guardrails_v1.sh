#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci wire indexed guardrails (v1) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py -m py_compile scripts/_patch_prove_ci_wire_indexed_guardrails_v1.py
./scripts/py scripts/_patch_prove_ci_wire_indexed_guardrails_v1.py

# safety: prove_ci must remain syntactically valid
bash -n scripts/prove_ci.sh

echo "OK"
