#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

./scripts/py scripts/_patch_wire_ci_milestone_latest_into_append_wrapper_v1.py

# Sanity: wrapper must remain bash-parseable
bash -n scripts/patch_add_ci_milestone_log_v1.sh
