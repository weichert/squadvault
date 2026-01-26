#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Editorial Attunement Layer v1 (EAL) ==="

# Self-check
bash -n "$0"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_add_editorial_attunement_layer_v1.py

python="${PYTHON:-python}"

# Unit tests (fast)
PYTHONPATH=src "$python" -m unittest -v \
  Tests/test_editorial_attunement_v1.py

# Repo-wide shell syntax guard
./scripts/check_shell_syntax.sh

echo "OK: EAL v1 patch applied and verified."
