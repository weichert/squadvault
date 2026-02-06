#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_golden_path guard selection fingerprint (v1) ==="

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
py="${repo_root}/scripts/py"

"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_prove_golden_path_guard_selection_fingerprint_v1.py"

echo "==> bash -n"
bash -n "${repo_root}/scripts/prove_golden_path.sh"
echo "OK: bash -n"

echo "==> grep confirm"
grep -n "SV_PATCH_GP_GUARD_SELECTION_FINGERPRINT_V1" -n "${repo_root}/scripts/prove_golden_path.sh"
echo "OK"
