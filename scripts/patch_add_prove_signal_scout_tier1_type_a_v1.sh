#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Signal Scout Tier-1 Type A proof + wire into CI (v1) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_add_prove_signal_scout_tier1_type_a_v1.py

echo "==> bash -n"
bash -n scripts/prove_signal_scout_tier1_type_a_v1.sh
bash -n scripts/prove_ci.sh

echo "OK"
