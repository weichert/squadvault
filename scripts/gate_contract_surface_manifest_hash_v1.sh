#!/usr/bin/env bash
set -euo pipefail

# Gate: contract surface manifest hash exactness (v1)
# - Regenerates manifest and requires no diff.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

target="docs/contracts/CONTRACT_SURFACE_MANIFEST_v1.json"
if [ ! -f "$target" ]; then
  echo "ERROR: missing manifest: $target"
  echo "Run: ./scripts/py scripts/gen_contract_surface_manifest_v1.py"
  exit 1
fi

tmp="$(mktemp)"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

./scripts/py scripts/gen_contract_surface_manifest_v1.py >/dev/null
git diff --exit-code -- "$target" >/dev/null || {
  echo "ERROR: contract surface manifest is out of date."
  echo "Fix by running:"
  echo "  ./scripts/py scripts/gen_contract_surface_manifest_v1.py"
  exit 1
}

echo "OK: contract surface manifest is canonical."
exit 0
