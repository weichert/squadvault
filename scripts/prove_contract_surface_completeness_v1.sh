#!/usr/bin/env bash
set -euo pipefail

echo "==> Proof: contract surface completeness gate (v1)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

bash scripts/gate_contract_surface_completeness_v1.sh

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "ERROR: Proof mutated repo or left working tree dirty." 1>&2
  git status --porcelain=v1 1>&2
  exit 1
fi

echo "OK"
