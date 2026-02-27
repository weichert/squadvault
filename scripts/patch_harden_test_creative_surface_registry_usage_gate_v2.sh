#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_harden_test_creative_surface_registry_usage_gate_v2.py
