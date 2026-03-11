#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_ci CWD gate logging + existence check (v1) ==="
python="${PYTHON:-python}"
./scripts/py scripts/_patch_prove_ci_cwd_gate_logging_v1.py
echo "==> bash -n"
bash -n scripts/prove_ci.sh
echo "OK"
