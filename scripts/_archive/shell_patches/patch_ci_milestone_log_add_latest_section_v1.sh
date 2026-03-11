#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

./scripts/py scripts/_patch_ci_milestone_log_add_latest_section_v1.py
