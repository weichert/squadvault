#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_gate_creative_surface_registry_usage_fix_truncation_v24.py
