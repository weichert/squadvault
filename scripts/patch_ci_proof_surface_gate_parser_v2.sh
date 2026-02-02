#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI proof surface gate parser hardening (v2) ==="

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${self_dir}/.." && pwd)"

py="${repo_root}/scripts/py"
if [[ -x "${py}" ]]; then
  "${py}" "${repo_root}/scripts/_patch_ci_proof_surface_gate_parser_v2.py"
else
  python="${PYTHON:-python}"
  "${python}" "${repo_root}/scripts/_patch_ci_proof_surface_gate_parser_v2.py"
fi

chmod +x "${repo_root}/scripts/check_ci_proof_surface_matches_registry_v1.sh"

echo "==> bash -n (gate)"
bash -n "${repo_root}/scripts/check_ci_proof_surface_matches_registry_v1.sh"

echo "OK: patch applied (v2)."
