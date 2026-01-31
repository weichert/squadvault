#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI cleanliness finishing touches (v1) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_ci_cleanliness_finishing_touches_v1.py

echo
echo "==> bash syntax check"
bash -n scripts/prove_ci.sh

echo "OK"
