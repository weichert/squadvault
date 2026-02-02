#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add banner to test DB routing gate (v1) ==="

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$self_dir/.." && pwd)"
cd "$repo_root"

python scripts/_patch_gate_enforce_test_db_routing_add_banner_v1.py

echo "==> bash -n gate script"
bash -n scripts/gate_enforce_test_db_routing_v1.sh

echo "OK"
