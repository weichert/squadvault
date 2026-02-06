#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: enforce canonical test DB routing (v2, line-based) ==="

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$self_dir/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_enforce_canonical_test_db_routing_v2.py

echo "==> bash -n (scripts/*.sh)"
bash -n scripts/gate_enforce_test_db_routing_v1.sh
bash -n scripts/patch_enforce_canonical_test_db_routing_v2.sh

echo "OK"
