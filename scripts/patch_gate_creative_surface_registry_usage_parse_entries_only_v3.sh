#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_gate_creative_surface_registry_usage_parse_entries_only_v3.py
