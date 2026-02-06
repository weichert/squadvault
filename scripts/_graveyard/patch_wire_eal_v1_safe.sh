#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Wire EAL v1 (safe seam) + cleanup duplicate import ==="

bash -n "$0"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_wire_eal_v1_safe.py

python="${PYTHON:-python}"

# Sanity: import the module that previously broke
PYTHONPATH=src "$python" -c "import scripts.recap as _; print('OK: import scripts.recap')"

# Full test suite (this is your standard)
PYTHONPATH=src "$python" -m pytest -q

./scripts/check_shell_syntax.sh

echo "OK: EAL wired + cleanup complete."
