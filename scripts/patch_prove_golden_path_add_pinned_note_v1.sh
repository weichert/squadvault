#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add pinned-block warning comment in prove_golden_path.sh (v1) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_prove_golden_path_add_pinned_note_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh

echo "==> verify note present"
grep -n '^# NOTE: do not replace with `pytest -q Tests`\.' scripts/prove_golden_path.sh >/dev/null

echo "OK"
