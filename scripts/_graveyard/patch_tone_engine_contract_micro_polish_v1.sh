#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: Tone Engine contract micro-polish (v1) ==="

python="${PYTHON:-python}"
"$python" scripts/_patch_tone_engine_contract_micro_polish_v1.py

echo "==> OK"
