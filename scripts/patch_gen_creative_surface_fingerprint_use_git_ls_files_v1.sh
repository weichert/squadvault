#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Patch: gen_creative_surface_fingerprint uses git ls-files (v1) ==="

python -m py_compile scripts/_patch_gen_creative_surface_fingerprint_use_git_ls_files_v1.py
./scripts/py scripts/_patch_gen_creative_surface_fingerprint_use_git_ls_files_v1.py

echo "==> sanity: generator runs"
./scripts/py scripts/gen_creative_surface_fingerprint_v1.py

echo "OK"
