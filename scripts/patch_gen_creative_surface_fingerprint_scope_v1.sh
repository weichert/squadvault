#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Pair wrapper for:
#   scripts/_patch_gen_creative_surface_fingerprint_scope_v1.py
#
# This repo enforces patcher/wrapper pairing for scripts/_patch_*.py via scripts/patch_*.sh.
# We delegate to the already-idempotent wrap_ runner to preserve behavior.

bash scripts/wrap_patch_gen_creative_surface_fingerprint_scope_v1.sh

# Sanity: bash syntax check
bash -n "$0"

echo "OK: patch_gen_creative_surface_fingerprint_scope_v1"
