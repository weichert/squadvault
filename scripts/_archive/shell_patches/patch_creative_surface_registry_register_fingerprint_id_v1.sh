#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_creative_surface_registry_register_fingerprint_id_v1.py
