#!/usr/bin/env bash
set -euo pipefail
bash -n "$0"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python -m py_compile scripts/_patch_add_gate_creative_surface_registry_usage_v1.py
python scripts/_patch_add_gate_creative_surface_registry_usage_v1.py

# basic safety: gate file should exist after patch
test -f scripts/gate_creative_surface_registry_usage_v1.sh
