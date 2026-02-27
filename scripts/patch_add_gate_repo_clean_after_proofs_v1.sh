#!/usr/bin/env bash
set -euo pipefail

# patch_add_gate_repo_clean_after_proofs_v1
# Idempotent wrapper: safe to run twice from clean.

repo_root="$(
  cd "$(dirname "$0")/.." >/dev/null 2>&1
  pwd
)"
cd "${repo_root}"

./scripts/py scripts/_patch_add_gate_repo_clean_after_proofs_v1.py
