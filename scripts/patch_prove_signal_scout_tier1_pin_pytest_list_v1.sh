#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: pin Signal Scout Tier-1 pytest surface to git-tracked list (v1) ==="
python="${PYTHON:-python}"

"$python" scripts/_patch_prove_signal_scout_tier1_pin_pytest_list_v1.py

echo "==> bash -n"
bash -n scripts/prove_signal_scout_tier1_type_a_v1.sh

echo "==> proof run"
./scripts/prove_signal_scout_tier1_type_a_v1.sh

echo "OK"
