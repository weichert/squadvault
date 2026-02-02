#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add CI proof surface registry + gate (v1) ==="

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${self_dir}/.." && pwd)"

py="${repo_root}/scripts/py"
if [[ -x "${py}" ]]; then
  "${py}" "${repo_root}/scripts/_patch_add_ci_proof_surface_registry_gate_v1.py"
else
  python="${PYTHON:-python}"
  "${python}" "${repo_root}/scripts/_patch_add_ci_proof_surface_registry_gate_v1.py"
fi

chmod +x "${repo_root}/scripts/check_ci_proof_surface_matches_registry_v1.sh"

echo "==> bash -n (new gate)"
bash -n "${repo_root}/scripts/check_ci_proof_surface_matches_registry_v1.sh"

echo "OK: patch applied (v1)."
