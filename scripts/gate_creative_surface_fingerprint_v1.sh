#!/usr/bin/env bash
set -euo pipefail

# Gate: creative surface fingerprint canonical (v1)
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

target="artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json"
if [ ! -f "$target" ]; then
  echo "ERROR: missing fingerprint file: $target"
  echo "Create it by running:"
  echo "  ./scripts/py scripts/gen_creative_surface_fingerprint_v1.py"
  exit 1
fi

./scripts/py scripts/gen_creative_surface_fingerprint_v1.py >/dev/null

git diff --exit-code -- "$target" >/dev/null || {
  echo "ERROR: creative surface fingerprint is out of date."
  echo "Fix by running:"
  echo "  ./scripts/py scripts/gen_creative_surface_fingerprint_v1.py"
  exit 1
}

echo "OK: creative surface fingerprint is canonical."
exit 0
