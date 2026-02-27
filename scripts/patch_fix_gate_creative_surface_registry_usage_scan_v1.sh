#!/usr/bin/env bash
set -euo pipefail

# patch_fix_gate_creative_surface_registry_usage_scan_v1
# Idempotent: safe to run twice.

repo_root="$(
  cd "$(dirname "$0")/.." >/dev/null 2>&1
  pwd
)"
cd "${repo_root}"

./scripts/py scripts/_patch_fix_gate_creative_surface_registry_usage_scan_v1.py
