#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci mktemp hardening + temp cleanup (v1) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_prove_ci_mktemp_hardening_v1.py

echo
echo "==> bash syntax check"
bash -n scripts/prove_ci.sh

echo "OK"
