#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: enforce canonical test DB routing (v1) ==="

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$self_dir/.." && pwd)"
cd "$repo_root"

python scripts/_patch_enforce_canonical_test_db_routing_v1.py

echo "==> bash -n (scripts/*.sh)"
bash -n scripts/gate_enforce_test_db_routing_v1.sh
bash -n scripts/patch_enforce_canonical_test_db_routing_v1.sh

echo "OK"
