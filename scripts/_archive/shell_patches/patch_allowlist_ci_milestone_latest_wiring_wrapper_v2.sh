#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

./scripts/py scripts/_patch_allowlist_ci_milestone_latest_wiring_wrapper_v2.py

# sanity: patcher must parse
python -m py_compile scripts/_patch_allowlist_ci_milestone_latest_wiring_wrapper_v2.py
