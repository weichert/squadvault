#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

./scripts/py scripts/_patch_fix_ci_milestone_log_require_clean_repo_v1.py

# Quick sanity: patched file must parse.
python -m py_compile scripts/_patch_add_ci_milestone_log_v1.py
