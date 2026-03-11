#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: preserve creative fingerprint during artifacts cleanup (v1) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py -m py_compile scripts/_patch_prove_creative_determinism_preserve_fingerprint_v1.py
./scripts/py scripts/_patch_prove_creative_determinism_preserve_fingerprint_v1.py

bash -n scripts/prove_creative_determinism_v1.sh
echo "OK"
