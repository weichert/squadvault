#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: _get_recap_run_trace optional EAL return contract (v1) ==="

bash -n "$0"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_fix_get_recap_run_trace_optional_eal_return_v1.py

python="${PYTHON:-python}"

# Sanity import
PYTHONPATH=src "$python" -c "from squadvault.recaps import weekly_recap_lifecycle as _; print('OK: import weekly_recap_lifecycle')"

# Targeted test
PYTHONPATH=src "$python" -m pytest -q Tests/test_get_recap_run_trace_optional_eal_v1.py

# Full suite
PYTHONPATH=src "$python" -m pytest -q

./scripts/check_shell_syntax.sh

echo "OK: trace return contract fixed and verified."
