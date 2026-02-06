#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_golden_path keep export tmp dir via SV_KEEP_EXPORT_TMP (v1) ==="

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
py="${repo_root}/scripts/py"

"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_prove_golden_path_keep_exports_tmp_v1.py"

echo "==> bash -n"
bash -n scripts/prove_golden_path.sh
echo "OK"
