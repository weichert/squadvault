#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_add_ci_milestone_log_v1.py

# <!-- SV_CI_MILESTONE_LATEST_WIRED_v1_BEGIN -->

# Also refresh the 'Latest' section so the log stays navigable.
./scripts/py scripts/_patch_ci_milestone_log_add_latest_section_v1.py

# <!-- SV_CI_MILESTONE_LATEST_WIRED_v1_END -->
