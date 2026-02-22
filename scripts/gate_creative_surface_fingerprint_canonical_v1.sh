#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "=== Gate: Creative surface fingerprint canonical (v1) ==="

target="artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json"

if [[ ! -f "${target}" ]]; then
  echo "ERROR: missing fingerprint file: ${target}"
  echo "Create it by running:"
  echo "  ./scripts/py scripts/gen_creative_surface_fingerprint_v1.py"
  exit 1
fi

# Snapshot the target before.
before_sha="$(shasum -a 256 "${target}" | awk '{print $1}')"

# Run generator (should noop when canonical).
./scripts/py scripts/gen_creative_surface_fingerprint_v1.py

# Snapshot after.
after_sha="$(shasum -a 256 "${target}" | awk '{print $1}')"

if [[ "${before_sha}" != "${after_sha}" ]]; then
  echo "FAIL: creative surface fingerprint drift detected."
  echo
  echo "==> git status --porcelain=v1"
  git status --porcelain=v1 || true
  echo
  echo "==> git diff --name-only"
  git diff --name-only -- "${target}" || true
  echo
  echo "==> git diff --stat"
  git diff --stat -- "${target}" || true
  exit 1
fi

echo "OK: creative surface fingerprint is canonical."
