#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: schema.sql add recap_runs.editorial_attunement_v1 (v1) ==="

bash -n "$0"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_schema_add_recap_runs_eal_v1.py

python="${PYTHON:-python}"

# Fast check: run tests + proof mode
PYTHONPATH=src "$python" -m pytest -q
./scripts/prove_golden_path.sh

./scripts/check_shell_syntax.sh

echo "OK: schema updated + verified."
