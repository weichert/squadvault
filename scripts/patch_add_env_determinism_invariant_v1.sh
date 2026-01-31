#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add ENV determinism invariant + index entry (v1) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -x "./scripts/py" ]]; then
  ./scripts/py scripts/_patch_add_env_determinism_invariant_v1.py
else
  python scripts/_patch_add_env_determinism_invariant_v1.py
fi

echo "==> bash -n (sanity)"
bash -n scripts/patch_add_env_determinism_invariant_v1.sh
echo "OK"
